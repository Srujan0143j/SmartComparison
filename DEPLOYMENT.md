# How to Deploy SmartCompare for Public Access (Zero-Config)

This guide provides step-by-step instructions for deploying the **entire project** (both FastAPI backend and HTML frontend) to the cloud using **Vercel**—completely free and with **zero database configuration required**.

---

## How It Works
We have updated the backend to support a local JSON file database fallback. 
- If no external MongoDB connection string is provided (or if local MongoDB is unreachable), the application automatically falls back to reading from a bundled `products.json` file inside the repository.
- This means you can deploy the complete project to Vercel in 1-click **without setting up MongoDB Atlas** or **configuring any environment variables**!

---

## Step 1: Deploy Everything on Vercel

1. Sign up/log in to [Vercel](https://vercel.com/) using your GitHub account.
2. Click **Add New** -> **Project**.
3. Select your `SmartComparison` repository from the list.
4. In the **Configure Project** section:
   - Leave the **Root Directory** as the repository root `./` (do not change it to `frontend` or `backend`). Vercel will automatically detect `vercel.json` and build both parts!
   - You **do not** need to add any Environment Variables.
5. Click **Deploy**.
   - Vercel will build your static frontend assets and install the Python dependencies for your serverless backend.
   - Once completed, Vercel will give you a public URL (e.g., `https://smart-comparison.vercel.app`).

Your SmartCompare website is now 100% public and fully functional. You can search, compare, and browse all products instantly!
