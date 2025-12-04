"""
Aurora Latent Space Extraction and Analysis

This script demonstrates how to extract and analyze Aurora's latent space representations 
during temperature (t2m) prediction.

What is Aurora's Latent Space?
- Input: Complex weather data (temperature, wind, pressure, etc.)
- Latent Space: Compressed vectors that capture essential weather patterns  
- Output: Future weather predictions

Flow: Physical Weather → Encoder → Latent Vectors → Decoder → Future Weather
           (t2m)                    (512-dim)              (predicted t2m)
"""

import torch
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import xarray as xr
from datetime import datetime

# Aurora imports
from aurora import Aurora, Batch, Metadata, rollout

# Global storage for captured latent representations
latent_representations = []
backbone_features = []
decoder_inputs = []

def capture_encoder_output(module, input, output):
    """Capture the encoder output (latent space after encoding)"""
    global latent_representations
    latent_representations.append(output.detach().cpu().clone())
    print(f"Captured encoder latent space: {output.shape}")
    return output

def capture_backbone_output(module, input, output):
    """Capture the backbone output (processed latent space)"""
    global backbone_features
    backbone_features.append(output.detach().cpu().clone())
    print(f"Captured backbone features: {output.shape}")
    return output

def capture_decoder_input(module, input, output):
    """Capture the input to decoder (processed latent space)"""
    global decoder_inputs
    # input[0] is the processed latent representation going into decoder
    decoder_inputs.append(input[0].detach().cpu().clone())
    print(f"Captured decoder input: {input[0].shape}")
    return output

def setup_latent_hooks(model):
    """Register hooks to capture latent representations at different stages"""
    hooks = []
    
    # Hook the encoder output (initial latent space)
    hooks.append(model.encoder.register_forward_hook(capture_encoder_output))
    
    # Hook the backbone output (processed latent space)
    hooks.append(model.backbone.register_forward_hook(capture_backbone_output))
    
    # Hook the decoder input
    hooks.append(model.decoder.register_forward_hook(capture_decoder_input))
    
    return hooks

def clear_captured_data():
    """Clear all captured representations"""
    global latent_representations, backbone_features, decoder_inputs
    latent_representations.clear()
    backbone_features.clear()
    decoder_inputs.clear()

def load_era5_data(download_path):
    """Load ERA5 data from downloaded files"""
    download_path = Path(download_path).expanduser()
    
    # Check if data exists
    required_files = ["static.nc", "2023-01-01-surface-level.nc", "2023-01-01-atmospheric.nc"]
    for file in required_files:
        if not (download_path / file).exists():
            raise FileNotFoundError(f"{file} not found in {download_path}")
        else:
            print(f"✓ Found {file}")
    
    # Load the datasets
    static_vars_ds = xr.open_dataset(download_path / "static.nc", engine="netcdf4")
    surf_vars_ds = xr.open_dataset(download_path / "2023-01-01-surface-level.nc", engine="netcdf4")
    atmos_vars_ds = xr.open_dataset(download_path / "2023-01-01-atmospheric.nc", engine="netcdf4")
    
    return static_vars_ds, surf_vars_ds, atmos_vars_ds

def create_aurora_batch(static_vars_ds, surf_vars_ds, atmos_vars_ds):
    """Create Aurora batch from ERA5 datasets"""
    batch = Batch(
        surf_vars={
            # t2m = 2-meter temperature (what you're interested in!)
            "2t": torch.from_numpy(surf_vars_ds["t2m"].values[:2][None]),
            "10u": torch.from_numpy(surf_vars_ds["u10"].values[:2][None]),
            "10v": torch.from_numpy(surf_vars_ds["v10"].values[:2][None]),
            "msl": torch.from_numpy(surf_vars_ds["msl"].values[:2][None]),
        },
        static_vars={
            "z": torch.from_numpy(static_vars_ds["z"].values[0]),
            "slt": torch.from_numpy(static_vars_ds["slt"].values[0]),
            "lsm": torch.from_numpy(static_vars_ds["lsm"].values[0]),
        },
        atmos_vars={
            "t": torch.from_numpy(atmos_vars_ds["t"].values[:2][None]),
            "u": torch.from_numpy(atmos_vars_ds["u"].values[:2][None]),
            "v": torch.from_numpy(atmos_vars_ds["v"].values[:2][None]),
            "q": torch.from_numpy(atmos_vars_ds["q"].values[:2][None]),
            "z": torch.from_numpy(atmos_vars_ds["z"].values[:2][None]),
        },
        metadata=Metadata(
            lat=torch.from_numpy(surf_vars_ds.latitude.values),
            lon=torch.from_numpy(surf_vars_ds.longitude.values),
            time=(surf_vars_ds.valid_time.values.astype("datetime64[s]").tolist()[1],),
            atmos_levels=tuple(int(level) for level in atmos_vars_ds.pressure_level.values),
        ),
    )
    
    return batch

def analyze_latent_space(latent):
    """Analyze the latent space representation"""
    print("\n🧠 AURORA'S LATENT SPACE ANALYSIS")
    print("=" * 50)
    print(f"Latent tensor shape: {latent.shape}")
    print(f"  - Batch size: {latent.shape[0]}")
    print(f"  - Number of latent tokens: {latent.shape[1]:,}")
    print(f"  - Embedding dimension: {latent.shape[2]}")
    print(f"  - Total latent parameters: {latent.numel():,}")
    
    print(f"\n📈 LATENT VECTOR STATISTICS")
    print(f"  - Mean: {latent.mean().item():.6f}")
    print(f"  - Standard deviation: {latent.std().item():.6f}")
    print(f"  - Min value: {latent.min().item():.6f}")
    print(f"  - Max value: {latent.max().item():.6f}")
    
    print(f"\n🌡️  WHAT THESE NUMBERS REPRESENT:")
    print(f"Each of the {latent.shape[1]:,} tokens is a {latent.shape[2]}-dimensional vector that encodes:")
    print(f"  • Temperature patterns from your t2m data")
    print(f"  • Wind patterns (10u, 10v)")
    print(f"  • Pressure patterns (msl)")
    print(f"  • Atmospheric conditions at multiple pressure levels")
    print(f"  • Spatial relationships between these variables")
    
    print(f"\nThink of each token as a 'weather concept' that Aurora uses to understand and predict!")

def visualize_latent_space(latent, title="Aurora's Latent Space for Temperature Prediction"):
    """Create comprehensive visualizations of the latent space"""
    try:
        from sklearn.decomposition import PCA
    except ImportError:
        print("Warning: sklearn not available. Skipping PCA visualization.")
        PCA = None
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Flatten for easier analysis: (batch * num_tokens, embed_dim)
    latent_flat = latent.view(-1, latent.shape[-1])
    
    # 1. Heatmap of latent tokens (subset)
    subset_size = min(100, latent_flat.shape[0])
    embed_subset = min(50, latent.shape[-1])
    im1 = axes[0,0].imshow(latent_flat[:subset_size, :embed_subset].numpy(), 
                          aspect='auto', cmap='RdBu_r', vmin=-2, vmax=2)
    axes[0,0].set_title(f'Latent Embeddings\n({subset_size} tokens × {embed_subset} dims)')
    axes[0,0].set_xlabel('Embedding Dimension')
    axes[0,0].set_ylabel('Latent Token')
    plt.colorbar(im1, ax=axes[0,0])
    
    # 2. Distribution of all latent values
    axes[0,1].hist(latent_flat.numpy().flatten(), bins=50, alpha=0.7, color='skyblue')
    axes[0,1].set_title('Distribution of All Latent Values')
    axes[0,1].set_xlabel('Latent Value')
    axes[0,1].set_ylabel('Frequency')
    axes[0,1].axvline(0, color='red', linestyle='--', alpha=0.7, label='Zero')
    axes[0,1].legend()
    
    # 3. Average embedding value per token
    token_means = latent_flat.mean(dim=1)
    axes[0,2].plot(token_means.numpy(), alpha=0.8, color='green')
    axes[0,2].set_title('Average Embedding per Token')
    axes[0,2].set_xlabel('Token Index')
    axes[0,2].set_ylabel('Mean Embedding Value')
    axes[0,2].grid(True, alpha=0.3)
    
    # 4. Variance across embedding dimensions
    dim_vars = latent_flat.var(dim=0)
    axes[1,0].plot(dim_vars.numpy(), alpha=0.8, color='purple')
    axes[1,0].set_title('Variance Across Embedding Dimensions')
    axes[1,0].set_xlabel('Embedding Dimension')
    axes[1,0].set_ylabel('Variance')
    axes[1,0].grid(True, alpha=0.3)
    
    # 5. Token similarity matrix (subset)
    token_subset = latent_flat[:50]  # First 50 tokens
    similarity = torch.nn.functional.cosine_similarity(
        token_subset.unsqueeze(1), token_subset.unsqueeze(0), dim=2
    )
    im2 = axes[1,1].imshow(similarity.numpy(), cmap='coolwarm', vmin=-1, vmax=1)
    axes[1,1].set_title('Token Similarity Matrix\n(Cosine Similarity, 50×50)')
    axes[1,1].set_xlabel('Token Index')
    axes[1,1].set_ylabel('Token Index')
    plt.colorbar(im2, ax=axes[1,1])
    
    # 6. Principal components (first 2 PCs of tokens)
    if PCA is not None:
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(latent_flat.numpy())
        
        scatter = axes[1,2].scatter(pca_result[:, 0], pca_result[:, 1], 
                                   alpha=0.6, c=range(len(pca_result)), cmap='viridis', s=10)
        axes[1,2].set_title(f'Latent Space PCA\n(Explained variance: {pca.explained_variance_ratio_.sum():.3f})')
        axes[1,2].set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.3f})')
        axes[1,2].set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.3f})')
        plt.colorbar(scatter, ax=axes[1,2], label='Token Index')
    else:
        axes[1,2].text(0.5, 0.5, 'PCA not available\n(sklearn required)', 
                       ha='center', va='center', transform=axes[1,2].transAxes)
        axes[1,2].set_title('PCA Visualization')
    
    plt.tight_layout()
    plt.suptitle(title, y=1.02, fontsize=16, fontweight='bold')
    plt.savefig('aurora_latent_space_visualization.png', dpi=150, bbox_inches='tight')
    plt.show()

def visualize_temperature_prediction(batch, pred):
    """Compare input vs predicted temperature"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Input temperature (most recent timestep) - move to CPU first
    input_temp = batch.surf_vars["2t"][0, -1].cpu().numpy() - 273.15  # Convert to Celsius
    pred_temp = pred.surf_vars["2t"][0, 0].cpu().numpy() - 273.15
    
    # Handle potential shape mismatch (cropping during processing)
    if input_temp.shape != pred_temp.shape:
        print(f"Shape mismatch detected: input {input_temp.shape} vs pred {pred_temp.shape}")
        # Crop input to match prediction size
        h_diff = input_temp.shape[0] - pred_temp.shape[0]
        w_diff = input_temp.shape[1] - pred_temp.shape[1]
        if h_diff > 0:
            input_temp = input_temp[:-h_diff, :]
        if w_diff > 0:
            input_temp = input_temp[:, :-w_diff]
        print(f"Cropped input to: {input_temp.shape}")
    
    temp_diff = pred_temp - input_temp

    # Plot input temperature
    im1 = axes[0].imshow(input_temp, vmin=-50, vmax=50, cmap='RdBu_r')
    axes[0].set_title(f'Input Temperature\n{batch.metadata.time[0]}')
    axes[0].set_xticks([])
    axes[0].set_yticks([])
    plt.colorbar(im1, ax=axes[0], label='°C')

    # Plot predicted temperature
    im2 = axes[1].imshow(pred_temp, vmin=-50, vmax=50, cmap='RdBu_r')
    axes[1].set_title(f'Predicted Temperature\n{pred.metadata.time[0]}')
    axes[1].set_xticks([])
    axes[1].set_yticks([])
    plt.colorbar(im2, ax=axes[1], label='°C')

    # Plot temperature difference
    im3 = axes[2].imshow(temp_diff, vmin=-5, vmax=5, cmap='RdBu_r')
    axes[2].set_title('Temperature Change\n(Predicted - Input)')
    axes[2].set_xticks([])
    axes[2].set_yticks([])
    plt.colorbar(im3, ax=axes[2], label='°C')

    plt.suptitle('Aurora Temperature Prediction from Latent Space Processing', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('aurora_temperature_prediction.png', dpi=150, bbox_inches='tight')
    plt.show()

    print(f"\n🌡️  TEMPERATURE ANALYSIS:")
    print(f"Input temperature range: {input_temp.min():.1f}°C to {input_temp.max():.1f}°C")
    print(f"Predicted temperature range: {pred_temp.min():.1f}°C to {pred_temp.max():.1f}°C")
    print(f"Temperature change range: {temp_diff.min():.1f}°C to {temp_diff.max():.1f}°C")
    print(f"Mean temperature change: {temp_diff.mean():.3f}°C")

def main():
    """Main function to run the latent space extraction"""
    print("🚀 Aurora Latent Space Extraction Starting...")
    
    # Path to downloaded ERA5 data - using your LatentSpace/data directory
    download_path = "/home/qhuang62/aurora-extreme-predictability/research/LatentSpace/data"
    
    try:
        # Load ERA5 data
        print("\n📁 Loading ERA5 data...")
        static_vars_ds, surf_vars_ds, atmos_vars_ds = load_era5_data(download_path)
        print("Data loaded successfully!")
        
        # Create Aurora batch
        print("\n🔧 Creating Aurora batch...")
        batch = create_aurora_batch(static_vars_ds, surf_vars_ds, atmos_vars_ds)
        print(f"Batch created successfully!")
        print(f"Input temperature shape: {batch.surf_vars['2t'].shape}")
        print(f"Temperature range: {batch.surf_vars['2t'].min():.1f}K to {batch.surf_vars['2t'].max():.1f}K")
        print(f"(In Celsius: {batch.surf_vars['2t'].min()-273.15:.1f}°C to {batch.surf_vars['2t'].max()-273.15:.1f}°C)")
        
        # Load Aurora model
        print("\n🤖 Loading Aurora model...")
        model = Aurora(use_lora=False)
        model.load_checkpoint("microsoft/aurora", "aurora-0.25-pretrained.ckpt")
        model.eval()
        
        # Check GPU availability and move model to GPU
        if torch.cuda.is_available():
            device = "cuda"
            model = model.to(device)
            print(f"🚀 Using GPU: {torch.cuda.get_device_name()}")
            print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        else:
            device = "cpu"
            print("⚠️  GPU not available, using CPU (will be slower)")
        
        print("Aurora model loaded successfully!")
        print(f"Model device: {next(model.parameters()).device}")
        print(f"Model dtype: {next(model.parameters()).dtype}")
        
        # Clear any previous captures
        clear_captured_data()
        
        # Setup hooks to capture latent space
        hooks = setup_latent_hooks(model)
        
        # Move batch to same device as model
        batch = batch.to(device)
        
        print("\n🚀 Running Aurora with latent space extraction...")
        print("This will capture the internal representations as Aurora processes your temperature data!\n")
        
        # Run prediction and capture latent space
        with torch.inference_mode():
            pred = model(batch)
        
        print(f"\n✅ Prediction completed!")
        print(f"Predicted temperature shape: {pred.surf_vars['2t'].shape}")
        
        # Clean up hooks
        for hook in hooks:
            hook.remove()
        
        print(f"\n📊 Captured representations:")
        print(f"- Encoder outputs: {len(latent_representations)}")
        print(f"- Backbone features: {len(backbone_features)}")
        print(f"- Decoder inputs: {len(decoder_inputs)}")
        
        # Analyze the latent space
        if latent_representations:
            latent = latent_representations[0]
            analyze_latent_space(latent)
            
            # Create visualizations
            print("\n🎨 Creating visualizations...")
            visualize_latent_space(latent)
            visualize_temperature_prediction(batch, pred)
            
            # Save results
            print("\n💾 Saving results...")
            input_temp = batch.surf_vars["2t"][0, -1].cpu().numpy() - 273.15
            pred_temp = pred.surf_vars["2t"][0, 0].cpu().numpy() - 273.15
            
            # Handle shape mismatch for saving
            if input_temp.shape != pred_temp.shape:
                h_diff = input_temp.shape[0] - pred_temp.shape[0]
                w_diff = input_temp.shape[1] - pred_temp.shape[1]
                if h_diff > 0:
                    input_temp = input_temp[:-h_diff, :]
                if w_diff > 0:
                    input_temp = input_temp[:, :-w_diff]
            
            save_data = {
                'encoder_latent': latent_representations[0] if latent_representations else None,
                'backbone_features': backbone_features[0] if backbone_features else None,
                'decoder_inputs': decoder_inputs[0] if decoder_inputs else None,
                'input_batch': batch.to("cpu"),  # Move to CPU for saving
                'prediction': pred.to("cpu"),   # Move to CPU for saving
                'metadata': {
                    'model_config': 'aurora-0.25-pretrained',
                    'timestamp': str(batch.metadata.time[0]),
                    'input_temp_range_celsius': (float(input_temp.min()), float(input_temp.max())),
                    'predicted_temp_range_celsius': (float(pred_temp.min()), float(pred_temp.max())),
                    'latent_shape': latent_representations[0].shape if latent_representations else None,
                }
            }
            
            save_path = 'aurora_latent_analysis.pt'
            torch.save(save_data, save_path)
            print(f"💾 Latent space analysis saved to: {save_path}")
            print(f"You can load this data later with: torch.load('{save_path}')")
            
        else:
            print("❌ No latent representations captured. Check the hook setup.")
            
        print("\n🎉 Aurora latent space extraction completed!")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Please run the ERA5 download from docs/example_era5.ipynb first")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()