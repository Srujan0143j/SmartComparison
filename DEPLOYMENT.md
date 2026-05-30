# How to Deploy SmartCompare for Public Access (Without Render)

This guide provides step-by-step instructions for deploying the **entire project** (both FastAPI backend and HTML frontend) to the cloud using **Vercel** and **MongoDB Atlas**—completely free and without needing Render.

---

## Architecture Overview
By utilizing Vercel's support for Python Serverless Functions, we can host the frontend and backend together under a single Vercel deployment:
1. **Cloud Database:** Move from local MongoDB to a free **MongoDB Atlas** cloud database.
2. **Unified Deployment (Vercel):**
   - Vercel hosts your static frontend files (`frontend/*`).
   - Vercel automatically deploys your FastAPI Python backend (`api/index.py`) as serverless functions.
   - You only have one deployment, one URL, and zero CORS issues!

---

## Step 1: Migrate to MongoDB Atlas (Cloud Database)
To run your project in the cloud, you need a cloud MongoDB database instead of your local MongoDB.

1. Sign up/log in to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Click **Create** to deploy a new cluster:
   - Select the **M0 Free** tier.
   - Choose a provider (e.g., AWS) and region closest to your users.
3. Configure Security:
   - Create a **database user** with a username and password (write this down).
   - Under **Network Access**, select **Add IP Address** and choose **Allow Access From Anywhere** (`0.0.0.0/0`). This ensures Vercel's serverless functions can connect.
4. Get your connection string:
   - Go to the Atlas Dashboard -> click **Connect** -> select **Drivers**.
   - Copy the connection string. It will look like this:
     ```text
     mongodb+srv://<username>:<password>@cluster0.xxxxxx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
     ```
     *(Be sure to replace `<username>` and `<password>` with the credentials of the database user you created)*.

---

## Step 2: Push the Updated Files to GitHub
We have configured your project with `vercel.json`, `api/index.py`, and updated the URL handling in `frontend/js/app.js` to dynamically support Vercel serverless functions without needing any code edits.

Let's commit and push these files to your repository:
```bash
git add .
git commit -m "Configure Vercel serverless deployment"
git push origin main
```

---

## Step 3: Deploy Everything on Vercel

1. Sign up/log in to [Vercel](https://vercel.com/) using your GitHub account.
2. Click **Add New** -> **Project**.
3. Select your `SmartComparison` repository from the list.
4. In the **Configure Project** section:
   - Leave the **Root Directory** as the repository root `./` (do not change it to `frontend` or `backend`). Vercel will automatically detect `vercel.json` and build both parts!
5. Expand the **Environment Variables** section and add the following:
   - **Key:** `MONGO_URI`
   - **Value:** Paste your MongoDB connection string from Step 1.
   - **Key:** `DB_NAME`
   - **Value:** `smartcompare_db`
6. Click **Deploy**.
   - Vercel will build your static frontend assets and install the python dependencies for your serverless backend.
   - Once completed, Vercel will give you a public URL (e.g., `https://smart-comparison.vercel.app`).

Your SmartCompare application is now fully public, connected to a cloud database, and accessible worldwide under a single URL!
