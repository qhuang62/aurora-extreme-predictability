"""
Hurricane vs Normal Weather Latent Space Comparison

This script extracts Aurora's latent space representations during Typhoon Nanmadol
and compares them with normal weather conditions to test the hypothesis that
extreme weather events occupy distinct regions in latent space.

Comparison:
- Normal Weather: Jan 1, 2023 (from previous analysis)
- Extreme Weather: Typhoon Nanmadol, Sep 17, 2022
"""

import torch
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import xarray as xr
from datetime import datetime
import fsspec

# Aurora imports
from aurora import Aurora, Batch, Metadata

# Global storage for captured latent representations
hurricane_latents = []
hurricane_backbone = []
hurricane_decoder = []

def capture_hurricane_encoder(module, input, output):
    """Capture hurricane encoder output"""
    global hurricane_latents
    hurricane_latents.append(output.detach().cpu().clone())
    print(f"Captured hurricane encoder latent: {output.shape}")
    return output

def capture_hurricane_backbone(module, input, output):
    """Capture hurricane backbone output"""
    global hurricane_backbone
    hurricane_backbone.append(output.detach().cpu().clone())
    print(f"Captured hurricane backbone features: {output.shape}")
    return output

def capture_hurricane_decoder(module, input, output):
    """Capture hurricane decoder input"""
    global hurricane_decoder
    hurricane_decoder.append(input[0].detach().cpu().clone())
    print(f"Captured hurricane decoder input: {input[0].shape}")
    return output

def setup_hurricane_hooks(model):
    """Register hooks for hurricane latent capture"""
    hooks = []
    hooks.append(model.encoder.register_forward_hook(capture_hurricane_encoder))
    hooks.append(model.backbone.register_forward_hook(capture_hurricane_backbone))
    hooks.append(model.decoder.register_forward_hook(capture_hurricane_decoder))
    return hooks

def clear_hurricane_data():
    """Clear captured hurricane data"""
    global hurricane_latents, hurricane_backbone, hurricane_decoder
    hurricane_latents.clear()
    hurricane_backbone.clear()
    hurricane_decoder.clear()

def load_hurricane_data():
    """Load Typhoon Nanmadol data (following finetune_nanmadol_2022_init12.ipynb pattern)"""
    # Path to hurricane data
    download_path = Path("/home/qhuang62/aurora-extreme-predictability/research/TC/data/hresT0_nanmadol_2022")
    
    print(f"Loading hurricane data from: {download_path}")
    
    # Check if data exists
    day = "2022-09-17"
    required_files = [
        f"{day}-surface-level.nc",
        f"{day}-atmospheric.nc", 
        "static.nc"
    ]
    
    for file in required_files:
        if not (download_path / file).exists():
            print(f"❌ {file} not found. Please run the hurricane data download first.")
            return None, None, None
        else:
            print(f"✅ Found {file}")
    
    # Load datasets
    static_vars_ds = xr.open_dataset(download_path / "static.nc", engine="netcdf4")
    surf_vars_ds = xr.open_dataset(download_path / f"{day}-surface-level.nc", engine="netcdf4")
    atmos_vars_ds = xr.open_dataset(download_path / f"{day}-atmospheric.nc", engine="netcdf4")
    
    return static_vars_ds, surf_vars_ds, atmos_vars_ds

def create_hurricane_batch(static_vars_ds, surf_vars_ds, atmos_vars_ds):
    """Create hurricane batch (following finetune_nanmadol_2022_init12.ipynb pattern)"""
    
    def _prepare(x: np.ndarray) -> torch.Tensor:
        """Prepare HRES variable - requires latitude flipping and time selection"""
        # Select time points 1 and 2 (06:00 and 12:00) for 12:00 UTC initialization
        return torch.from_numpy(x[[1, 2]][None][..., ::-1, :].copy())
    
    batch = Batch(
        surf_vars={
            "2t": _prepare(surf_vars_ds["2m_temperature"].values),
            "10u": _prepare(surf_vars_ds["10m_u_component_of_wind"].values),
            "10v": _prepare(surf_vars_ds["10m_v_component_of_wind"].values),
            "msl": _prepare(surf_vars_ds["mean_sea_level_pressure"].values),
        },
        static_vars={
            # Static vars from ERA5 don't need lat flipping
            "z": torch.from_numpy(static_vars_ds["z"].values[0]),
            "slt": torch.from_numpy(static_vars_ds["slt"].values[0]),
            "lsm": torch.from_numpy(static_vars_ds["lsm"].values[0]),
        },
        atmos_vars={
            "t": _prepare(atmos_vars_ds["temperature"].values),
            "u": _prepare(atmos_vars_ds["u_component_of_wind"].values),
            "v": _prepare(atmos_vars_ds["v_component_of_wind"].values),
            "q": _prepare(atmos_vars_ds["specific_humidity"].values),
            "z": _prepare(atmos_vars_ds["geopotential"].values),
        },
        metadata=Metadata(
            # Flip latitudes for HRES data
            lat=torch.from_numpy(surf_vars_ds.latitude.values[::-1].copy()),
            lon=torch.from_numpy(surf_vars_ds.longitude.values),
            # Use time point 2 for 12:00 UTC initialization (hurricane center time)
            time=(surf_vars_ds.time.values.astype("datetime64[s]").tolist()[2],),
            atmos_levels=tuple(int(level) for level in atmos_vars_ds.level.values),
        ),
    )
    
    return batch

def compare_latent_spaces(normal_latent, hurricane_latent):
    """Compare normal vs hurricane latent space representations"""
    print("\n🌀 HURRICANE vs NORMAL WEATHER LATENT COMPARISON")
    print("=" * 60)
    
    # Basic statistics comparison
    print("📊 BASIC STATISTICS:")
    print(f"Normal weather   - Mean: {normal_latent.mean():.6f}, Std: {normal_latent.std():.6f}")
    print(f"Hurricane        - Mean: {hurricane_latent.mean():.6f}, Std: {hurricane_latent.std():.6f}")
    print(f"Difference       - Mean: {hurricane_latent.mean() - normal_latent.mean():.6f}")
    print(f"Difference       - Std:  {hurricane_latent.std() - normal_latent.std():.6f}")
    
    # Distribution comparison
    normal_flat = normal_latent.view(-1)
    hurricane_flat = hurricane_latent.view(-1)
    
    print(f"\n📈 DISTRIBUTION COMPARISON:")
    print(f"Normal range:    [{normal_flat.min():.3f}, {normal_flat.max():.3f}]")
    print(f"Hurricane range: [{hurricane_flat.min():.3f}, {hurricane_flat.max():.3f}]")
    
    # Calculate cosine similarity between representations
    normal_mean = normal_latent.mean(dim=1)  # Average over tokens
    hurricane_mean = hurricane_latent.mean(dim=1)
    
    cosine_sim = torch.nn.functional.cosine_similarity(
        normal_mean.flatten(), hurricane_mean.flatten(), dim=0
    )
    print(f"\n🎯 OVERALL SIMILARITY:")
    print(f"Cosine similarity: {cosine_sim:.6f}")
    print(f"Interpretation: {1.0 - cosine_sim:.6f} dissimilarity")
    
    return normal_flat, hurricane_flat, cosine_sim

def visualize_comparison(normal_latent, hurricane_latent, normal_flat, hurricane_flat):
    """Create comprehensive comparison visualization"""
    
    try:
        from sklearn.decomposition import PCA
        from sklearn.manifold import TSNE
    except ImportError:
        print("Warning: sklearn not available. Skipping advanced visualizations.")
        PCA = TSNE = None
    
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    
    # 1. Distribution comparison
    axes[0,0].hist(normal_flat.numpy(), bins=50, alpha=0.7, color='blue', label='Normal', density=True)
    axes[0,0].hist(hurricane_flat.numpy(), bins=50, alpha=0.7, color='red', label='Hurricane', density=True)
    axes[0,0].set_title('Latent Value Distributions')
    axes[0,0].set_xlabel('Latent Value')
    axes[0,0].set_ylabel('Density')
    axes[0,0].legend()
    axes[0,0].grid(True, alpha=0.3)
    
    # 2. Box plot comparison
    data_to_plot = [normal_flat.numpy(), hurricane_flat.numpy()]
    box_plot = axes[0,1].boxplot(data_to_plot, labels=['Normal', 'Hurricane'], patch_artist=True)
    box_plot['boxes'][0].set_facecolor('lightblue')
    box_plot['boxes'][1].set_facecolor('lightcoral')
    axes[0,1].set_title('Distribution Comparison')
    axes[0,1].set_ylabel('Latent Value')
    axes[0,1].grid(True, alpha=0.3)
    
    # 3. Token mean comparison
    normal_token_means = normal_latent.mean(dim=2).flatten()
    hurricane_token_means = hurricane_latent.mean(dim=2).flatten()
    
    axes[0,2].plot(normal_token_means.numpy(), alpha=0.8, color='blue', label='Normal')
    axes[0,2].plot(hurricane_token_means.numpy(), alpha=0.8, color='red', label='Hurricane')
    axes[0,2].set_title('Token Mean Values')
    axes[0,2].set_xlabel('Token Index')
    axes[0,2].set_ylabel('Mean Latent Value')
    axes[0,2].legend()
    axes[0,2].grid(True, alpha=0.3)
    
    # 4. Variance comparison
    normal_var = normal_latent.var(dim=2).flatten()
    hurricane_var = hurricane_latent.var(dim=2).flatten()
    
    axes[0,3].scatter(normal_var.numpy(), hurricane_var.numpy(), alpha=0.6, s=10)
    axes[0,3].plot([0, max(normal_var.max(), hurricane_var.max())], 
                   [0, max(normal_var.max(), hurricane_var.max())], 'k--', alpha=0.5)
    axes[0,3].set_title('Token Variance: Normal vs Hurricane')
    axes[0,3].set_xlabel('Normal Weather Variance')
    axes[0,3].set_ylabel('Hurricane Variance')
    axes[0,3].grid(True, alpha=0.3)
    
    # 5. Heatmap comparison (subset)
    subset_size = min(100, normal_latent.shape[1])
    embed_subset = min(50, normal_latent.shape[2])
    
    normal_subset = normal_latent[0, :subset_size, :embed_subset]
    hurricane_subset = hurricane_latent[0, :subset_size, :embed_subset]
    
    im1 = axes[1,0].imshow(normal_subset.numpy(), aspect='auto', cmap='RdBu_r', vmin=-2, vmax=2)
    axes[1,0].set_title('Normal Weather Embeddings')
    axes[1,0].set_xlabel('Embedding Dimension')
    axes[1,0].set_ylabel('Token Index')
    plt.colorbar(im1, ax=axes[1,0])
    
    im2 = axes[1,1].imshow(hurricane_subset.numpy(), aspect='auto', cmap='RdBu_r', vmin=-2, vmax=2)
    axes[1,1].set_title('Hurricane Embeddings')
    axes[1,1].set_xlabel('Embedding Dimension')
    axes[1,1].set_ylabel('Token Index')
    plt.colorbar(im2, ax=axes[1,1])
    
    # 6. Difference heatmap
    diff_subset = hurricane_subset - normal_subset
    im3 = axes[1,2].imshow(diff_subset.numpy(), aspect='auto', cmap='RdBu_r', 
                          vmin=-1, vmax=1)
    axes[1,2].set_title('Difference (Hurricane - Normal)')
    axes[1,2].set_xlabel('Embedding Dimension') 
    axes[1,2].set_ylabel('Token Index')
    plt.colorbar(im3, ax=axes[1,2])
    
    # 7. PCA comparison if available
    if PCA is not None:
        # Combine data for joint PCA
        combined_data = torch.cat([
            normal_latent.view(-1, normal_latent.shape[-1]),
            hurricane_latent.view(-1, hurricane_latent.shape[-1])
        ], dim=0)
        
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(combined_data.numpy())
        
        # Split back
        n_normal = normal_latent.view(-1, normal_latent.shape[-1]).shape[0]
        normal_pca = pca_result[:n_normal]
        hurricane_pca = pca_result[n_normal:]
        
        axes[1,3].scatter(normal_pca[:, 0], normal_pca[:, 1], 
                         alpha=0.6, c='blue', label='Normal', s=10)
        axes[1,3].scatter(hurricane_pca[:, 0], hurricane_pca[:, 1], 
                         alpha=0.6, c='red', label='Hurricane', s=10)
        axes[1,3].set_title(f'PCA Comparison\n(Explained var: {pca.explained_variance_ratio_.sum():.3f})')
        axes[1,3].set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.3f})')
        axes[1,3].set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.3f})')
        axes[1,3].legend()
        axes[1,3].grid(True, alpha=0.3)
    else:
        axes[1,3].text(0.5, 0.5, 'PCA not available\n(sklearn required)', 
                      ha='center', va='center', transform=axes[1,3].transAxes)
        axes[1,3].set_title('PCA Comparison')
    
    plt.suptitle('Hurricane vs Normal Weather: Latent Space Comparison', 
                 fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('hurricane_vs_normal_latent_comparison.png', dpi=150, bbox_inches='tight')
    plt.show()

def main():
    """Main function for hurricane vs normal latent space comparison"""
    print("🌀 Hurricane vs Normal Weather Latent Space Analysis")
    print("=" * 60)
    
    try:
        # 1. Load previous normal weather analysis
        print("\n📁 Loading previous normal weather analysis...")
        try:
            normal_data = torch.load('aurora_latent_analysis.pt')
            normal_latent = normal_data['encoder_latent']
            print(f"✅ Loaded normal weather latent: {normal_latent.shape}")
        except FileNotFoundError:
            print("❌ Normal weather analysis not found. Please run aurora_latent_extraction.py first.")
            return
        
        # 2. Load hurricane data
        print("\n📁 Loading hurricane data...")
        static_vars_ds, surf_vars_ds, atmos_vars_ds = load_hurricane_data()
        if static_vars_ds is None:
            print("❌ Hurricane data not available. Please download first.")
            return
        
        # 3. Create hurricane batch
        print("\n🔧 Creating hurricane batch...")
        hurricane_batch = create_hurricane_batch(static_vars_ds, surf_vars_ds, atmos_vars_ds)
        print(f"Hurricane batch created for: {hurricane_batch.metadata.time[0]}")
        print(f"Hurricane MSL range: {hurricane_batch.surf_vars['msl'].min():.0f} - {hurricane_batch.surf_vars['msl'].max():.0f} Pa")
        
        # 4. Load Aurora model (use fine-tuned for HRES data)
        print("\n🤖 Loading Aurora model...")
        model = Aurora()  # Fine-tuned model for HRES data
        model.load_checkpoint("microsoft/aurora", "aurora-0.25-finetuned.ckpt")
        model.eval()
        
        # GPU setup
        if torch.cuda.is_available():
            device = "cuda"
            model = model.to(device)
            hurricane_batch = hurricane_batch.to(device)
            print(f"🚀 Using GPU: {torch.cuda.get_device_name()}")
        else:
            device = "cpu"
            print("⚠️ Using CPU (will be slower)")
        
        # 5. Extract hurricane latent space
        print("\n🌀 Extracting hurricane latent space...")
        clear_hurricane_data()
        hooks = setup_hurricane_hooks(model)
        
        with torch.inference_mode():
            hurricane_pred = model(hurricane_batch)
        
        # Clean up hooks
        for hook in hooks:
            hook.remove()
        
        if hurricane_latents:
            hurricane_latent = hurricane_latents[0]
            print(f"✅ Captured hurricane latent: {hurricane_latent.shape}")
            
            # 6. Compare latent spaces
            print("\n🔍 Comparing latent spaces...")
            normal_flat, hurricane_flat, cosine_sim = compare_latent_spaces(normal_latent, hurricane_latent)
            
            # 7. Create visualizations
            print("\n🎨 Creating comparison visualizations...")
            visualize_comparison(normal_latent, hurricane_latent, normal_flat, hurricane_flat)
            
            # 8. Save results
            print("\n💾 Saving hurricane analysis...")
            save_data = {
                'normal_latent': normal_latent,
                'hurricane_latent': hurricane_latent,
                'normal_batch': normal_data['input_batch'],
                'hurricane_batch': hurricane_batch.to("cpu"),
                'hurricane_prediction': hurricane_pred.to("cpu"),
                'comparison_metrics': {
                    'cosine_similarity': float(cosine_sim),
                    'dissimilarity': float(1.0 - cosine_sim),
                    'normal_stats': {
                        'mean': float(normal_latent.mean()),
                        'std': float(normal_latent.std()),
                        'min': float(normal_latent.min()),
                        'max': float(normal_latent.max()),
                    },
                    'hurricane_stats': {
                        'mean': float(hurricane_latent.mean()),
                        'std': float(hurricane_latent.std()),
                        'min': float(hurricane_latent.min()),
                        'max': float(hurricane_latent.max()),
                    }
                },
                'metadata': {
                    'normal_weather_date': str(normal_data['metadata']['timestamp']),
                    'hurricane_date': str(hurricane_batch.metadata.time[0]),
                    'model_used': 'aurora-0.25-finetuned',
                }
            }
            
            torch.save(save_data, 'hurricane_vs_normal_latent_analysis.pt')
            print("💾 Analysis saved to: hurricane_vs_normal_latent_analysis.pt")
            
            # 9. Summary
            print(f"\n🎉 ANALYSIS COMPLETE!")
            print(f"Key finding: {1.0 - cosine_sim:.3f} dissimilarity between normal and hurricane latent space")
            if cosine_sim < 0.8:
                print("✅ Hypothesis SUPPORTED: Hurricane and normal weather occupy distinct latent regions!")
            else:
                print("❓ Hypothesis unclear: More analysis needed to determine distinctness")
                
        else:
            print("❌ Failed to capture hurricane latent space")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()