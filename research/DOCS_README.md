# Research Documentation Guide

This directory contains the master documentation for the Aurora Extreme Weather Predictability project.

## Core Documents (READ THESE)

### 1. **RESEARCH_PLAN.md** (32 KB)
**Purpose**: Master research plan for the entire paper

**Contains**:
- Project overview and research questions
- Event selection strategy (12-15 events across 4 types)
- Experimental framework (two-stage approach)
- Metrics and evaluation methods
- Data organization and download requirements
- Visualization plan (7 main figures)
- Code infrastructure design
- Paper structure and timeline

**When to use**: 
- Starting analysis for a new event
- Understanding overall project goals
- Finding data requirements
- Planning paper figures

---

### 2. **EXPERIMENTAL_STRATEGY.md** (11 KB)
**Purpose**: Detailed explanation of the two-stage experimental approach

**Contains**:
- Strategy B rationale (variable initialization, fixed target)
- Stage 1: Lead time assessment (1, 3, 5, 7 days)
- Stage 2: Initialization sensitivity (00, 06, 12, 18 UTC)
- Complete Sandy example with pseudocode
- Data requirements calculation
- Comparison: Strategy A vs Strategy B

**When to use**:
- Understanding why we use variable initialization dates
- Implementing Stage 1 or Stage 2 scripts
- Explaining methodology to collaborators
- Planning data downloads for new events

---

## Event-Specific Documentation

### **TC/2012_Sandy/SANDY_DATA_WORKFLOW.md** (8.4 KB)
**Purpose**: Complete step-by-step workflow for Hurricane Sandy analysis

**Contains**:
- Two-stage experimental design for Sandy
- Data requirements (Oct 22-31, 2012)
- Download and combine scripts usage
- Analysis scripts execution order
- Troubleshooting guide

**When to use**:
- Running Sandy analysis from scratch
- Template for other TC events
- Debugging data issues

**Future**: Similar workflow docs for each major event

---

## Document History (What Was Removed)

**Deleted Documents**:
1. **IMPLEMENTATION_SUCCESS.md** - Obsolete progress log from Nov 10
2. **DATA_GUIDE.md** - Merged into RESEARCH_PLAN.md (data organization section)

**Why**: Reduce maintenance burden, eliminate duplication, clearer documentation structure

---

## Quick Reference

### "I want to..."

**...understand the project goals**
→ Read RESEARCH_PLAN.md (sections 1-2)

**...start analyzing a new event**
→ Read RESEARCH_PLAN.md (data organization) + EXPERIMENTAL_STRATEGY.md

**...understand the two-stage approach**
→ Read EXPERIMENTAL_STRATEGY.md

**...run Hurricane Sandy analysis**
→ Read TC/2012_Sandy/SANDY_DATA_WORKFLOW.md

**...download ERA5 data for an event**
→ RESEARCH_PLAN.md (data requirements table) + event workflow docs

**...create paper figures**
→ RESEARCH_PLAN.md (visualization plan, Figure 1-7 specs)

**...understand metrics**
→ RESEARCH_PLAN.md (metrics section)

---

**Last Updated**: November 10, 2025
**Documentation Status**: Consolidated and current
