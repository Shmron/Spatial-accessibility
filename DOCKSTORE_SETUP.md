# 🚀 Publishing to Dockstore - Complete Guide

## ✅ Files Created
- `.dockstore.yml` - Dockstore workflow configuration
- `test_params.json` - Test parameters for workflow validation

## 📋 STEP-BY-STEP GUIDE

### **STEP 1: Push Your Code to GitHub** ⬆️

```bash
cd ~/nf-tutorial

# Add new files
git add .dockstore.yml test_params.json

# Commit
git commit -m "Add Dockstore configuration for workflow publishing"

# Push to GitHub
git push origin main
```

---

### **STEP 2: Create a GitHub Release** 🏷️

1. Go to: https://github.com/Shmron/Spatial-accessibility
2. Click **"Releases"** on the right sidebar
3. Click **"Create a new release"**
4. Fill in:
   - **Tag version:** `v1.0.0`
   - **Release title:** `v1.0.0 - Initial Release`
   - **Description:**
     ```
     ## Spatial Accessibility Workflow v1.0.0

     First stable release of the containerized spatial accessibility analysis workflow.

     **Features:**
     - Dockerized analysis pipeline
     - OSRM routing for realistic travel distances
     - H3 hexagonal grid analysis
     - Automated summary statistics with actual administrative unit names
     - Production-ready visualizations

     **Docker Images:**
     - `shmronrsibs/spatial-analysis:v1.0`
     - `shmronrsibs/osrm-nextflow:v1.0`

     **Quick Start:**
     ```bash
     docker pull shmronrsibs/spatial-analysis:v1.0
     docker pull shmronrsibs/osrm-nextflow:v1.0
     ./run-workflow.sh
     ```
     ```
5. Click **"Publish release"**

---

### **STEP 3: Register on Dockstore** 📝

1. Go to: https://dockstore.org
2. Click **"Sign in with GitHub"**
3. Authorize Dockstore to access your GitHub account
4. Complete your profile

---

### **STEP 4: Register Your Workflow** 🔗

1. In Dockstore, click **"My Workflows"**
2. Click **"Register a Workflow"**
3. Select **"GitHub App"** (recommended)
4. Choose your repository: **`Shmron/Spatial-accessibility`**
5. Dockstore will automatically detect your `.dockstore.yml`
6. Click **"Add Workflow"**

---

### **STEP 5: Configure & Publish** 🎉

1. Your workflow appears in "My Workflows"
2. Click on it to view details
3. Dockstore reads your `.dockstore.yml` and displays:
   - Workflow name
   - Description
   - Labels
   - Author (you!)
   - ORCID
4. Click **"Publish"** to make it public
5. **Done!** Your workflow is now discoverable on Dockstore

---

## 🌐 YOUR DOCKSTORE URL

After publishing, your workflow will be available at:
```
https://dockstore.org/workflows/github.com/Shmron/Spatial-accessibility
```

---

## 🎯 WHAT USERS WILL SEE

When people find your workflow on Dockstore, they'll see:

**Workflow Card:**
- ⭐ Title: "spatial-accessibility-workflow"
- 👤 Author: Rutendo Sibanda (ORCID: 0009-0000-6835-2684)
- 🏷️ Labels: spatial-accessibility, health-equity, nextflow, docker, osrm, h3-grid
- 📝 Full description
- 🔗 Links to your GitHub repo
- 🐳 Docker Hub images
- 📊 Usage instructions

**They can:**
- Clone your repo
- Pull your Docker images
- Run your workflow with one command
- Cite your work properly (thanks to ORCID)

---

## 💡 TIPS FOR SUCCESS

### **Add a DOI (Optional but Recommended)**
1. Go to https://zenodo.org
2. Link your GitHub repository
3. Create a DOI for your release
4. Add the DOI badge to your README

### **Add Usage Examples**
Create a `docs/` folder with:
- Example datasets
- Expected outputs
- Troubleshooting guide

### **Keep It Updated**
When you make changes:
1. Push to GitHub
2. Create a new release (v1.1.0, etc.)
3. Dockstore automatically syncs!

---

## 🎓 BENEFITS OF DOCKSTORE

✅ **Discoverability** - Researchers can find your workflow
✅ **Citability** - Proper attribution with ORCID
✅ **Reproducibility** - Version control + containers = exact reproduction
✅ **Standardization** - Follows GA4GH standards
✅ **Integration** - Works with Terra, AnVIL, other platforms
✅ **Professional** - Shows you follow best practices

---

## 📊 METRICS YOU'LL GET

Dockstore tracks:
- Downloads
- Stars
- Forks
- Citations
- Usage across platforms

Great for your CV and grant applications! 📈

---

## 🆘 TROUBLESHOOTING

**"Dockstore can't find my workflow"**
- Make sure `.dockstore.yml` is in the repository root
- Check the file is committed and pushed to GitHub
- Verify the repository is public

**"Workflow validation failed"**
- Ensure `spatial_access_workflow.nf` exists
- Check `test_params.json` has valid parameters
- Make sure Docker images are public on Docker Hub

**"Can't connect GitHub"**
- Revoke and re-authorize Dockstore in GitHub settings
- Check repository permissions

---

## 🎯 NEXT STEPS AFTER PUBLISHING

1. **Share the link** on social media, papers, presentations
2. **Add the Dockstore badge** to your README:
   ```markdown
   [![Dockstore](https://img.shields.io/badge/Dockstore-Workflow-blue)](https://dockstore.org/workflows/github.com/Shmron/Spatial-accessibility)
   ```
3. **Submit to workflow registries** like WorkflowHub
4. **Write a blog post** or preprint about your workflow
5. **Present at conferences** - Dockstore makes it easy to share

---

## 📚 RESOURCES

- Dockstore Docs: https://docs.dockstore.org
- Nextflow + Dockstore: https://docs.dockstore.org/en/stable/getting-started/getting-started-with-nextflow.html
- GA4GH Standards: https://www.ga4gh.org

---

**You're ready to publish! This will make your workflow discoverable and citable by the global research community.** 🌍🔬