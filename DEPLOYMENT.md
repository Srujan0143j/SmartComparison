# How to Deploy SmartCompare for Public Access

This guide provides step-by-step instructions for deploying both the **FastAPI Backend** and the **HTML/CSS/JS Frontend** to the cloud so anyone can access your application over the internet.

---

## Architecture Overview
To transition from running locally (`localhost`) to a public deployment:
1. **Cloud Database:** Move from local MongoDB to a free **MongoDB Atlas** cloud database.
2. **Cloud Backend:** Host the FastAPI Python application on **Render** (free tier).
3. **Cloud Frontend:** Host the static frontend assets on **Vercel** or **Netlify** (free tiers, perfect for hosting from a subfolder).

---

## Step 1: Migrate to MongoDB Atlas (Cloud Database)
Render cannot access your local machine's MongoDB. You need a free cloud database.

1. Sign up/log in to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Click **Create** to deploy a new cluster:
   - Select the **M0 Free** tier.
   - Choose a provider (e.g., AWS) and region closest to your users.
3. Configure Security:
   - Create a **database user** with a username and password (write this down).
   - Under **Network Access**, select **Add IP Address** and choose **Allow Access From Anywhere** (`0.0.0.0/0`). This ensures Render's servers can connect.
4. Get your connection string:
   - Go to the Atlas Dashboard -> click **Connect** -> select **Drivers**.
   - Copy the connection string. It will look like this:
     ```text
     mongodb+srv://<username>:<password>@cluster0.xxxxxx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
     ```
     *(Be sure to replace `<username>` and `<password>` with the credentials of the database user you created)*.

---

## Step 2: Deploy the FastAPI Backend on Render
[Render](https://render.com/) is a cloud platform that integrates with GitHub to build and deploy web services.

1. Sign up/log in to [Render](https://render.com/).
2. Click **New +** (top right) -> **Web Service**.
3. Link your GitHub account and select your `SmartComparison` repository.
4. Configure your Web Service:
   - **Name:** `smartcompare-backend`
   - **Region:** Select a region close to your users.
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Set Environment Variables:
   - Click on the **Environment** tab.
   - Add a key `MONGO_URI` and paste your MongoDB connection string from Step 1.
   - Add a key `DB_NAME` with the value `smartcompare_db`.
6. Click **Create Web Service**.
   - Render will build and launch your API. Once running, copy the live URL provided at the top of the Render console (e.g., `https://smartcompare-backend.onrender.com`).

---

## Step 3: Update and Deploy the Frontend
Now, we must point your frontend code to the public URL of your new Render backend.

### 1. Update the Frontend URL
1. Open `frontend/js/app.js`.
2. Locate the first line:
   ```javascript
   const API_BASE = "http://localhost:8000";
   ```
3. Replace it with your public Render URL:
   ```javascript
   const API_BASE = "https://smartcompare-backend.onrender.com"; // Your Render URL
   ```
4. Commit and push the change to GitHub:
   ```bash
   git add frontend/js/app.js
   git commit -m "Update API endpoint to cloud Render URL"
   git push origin main
   ```

### 2. Host static files on Vercel (Simplest & Best for Subfolders)
Since the frontend is located inside the `frontend` folder rather than the root directory, **Vercel** is the easiest way to deploy:

1. Sign up/log in to [Vercel](https://vercel.com/) using your GitHub account.
2. Click **Add New** -> **Project**.
3. Select your `SmartComparison` repository.
4. Under **Configure Project**:
   - For **Root Directory**, click **Edit** and select the `frontend` folder.
   - Leave the rest as default (no build settings required as it's static HTML/CSS/JS).
5. Click **Deploy**.
   - Vercel will immediately publish your application and give you a public URL (e.g., `https://smart-comparison.vercel.app`).

Your SmartCompare application is now 100% public, connected to a cloud database, and accessible worldwide!
