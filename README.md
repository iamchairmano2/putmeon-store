# PUT ME ON — Clothing Store

A simple e-commerce storefront with an admin dashboard. Customers browse
products and add them to a bag; checkout doesn't take payment on the site —
instead it opens WhatsApp with a pre-filled order message sent straight to
your number.

Product photos are stored on **Cloudinary**, not on this server — so they
survive redeploys and restarts on hosts like Render (unlike a plain local
uploads folder, which gets wiped on the free tier).

## File structure

```
putmeon-store/
├── app.py                     Flask backend — all routes and logic
├── requirements.txt           Python dependencies
├── .env.example                Template for your Cloudinary credentials
├── .gitignore                  Keeps secrets and junk files out of GitHub
├── database.db                 Created automatically on first run
├── templates/
│   ├── index.html             Storefront (public)
│   ├── admin_login.html       Admin login page
│   └── admin_dashboard.html   Admin dashboard (add/edit/delete products)
└── static/
    ├── css/style.css          All styling
    ├── js/cart.js             Shopping bag + WhatsApp checkout logic
    └── js/admin.js            Small admin dashboard helper
```

Notice there's no `static/uploads/` folder — photos go straight to
Cloudinary instead of sitting on this server.

## Running it locally in VS Code

1. Open this folder in VS Code.
2. Open a terminal and run:
   ```
   pip install -r requirements.txt
   ```
3. **Set up your Cloudinary credentials:**
   - Copy `.env.example` to a new file named exactly `.env`
   - Open `.env` and paste in your real Cloud Name, API Key, and API
     Secret from your Cloudinary dashboard (`console.cloudinary.com` →
     Settings → API Keys)
   - `.env` is already git-ignored, so these stay private and never get
     pushed to GitHub
4. Run:
   ```
   python app.py
   ```
5. Open your browser to:
   - **Storefront:** http://127.0.0.1:5000/
   - **Admin login:** http://127.0.0.1:5000/admin/login

Default admin login (change this — see below):
- Username: `putmeon`
- Password: `changeme123`

## Before you go live — checklist

Open `app.py` and change these near the top of the file:

1. **`ADMIN_USERNAME` / `ADMIN_PASSWORD`** — set your own username and a
   strong password.
2. **`app.secret_key`** — replace with any long random string.
3. **`WHATSAPP_NUMBER`** — already set to `233596146157`. Update it here if
   the number ever changes.

## How to add products (as the admin)

1. Go to `/admin/login` and log in.
2. Fill in the name, price, and optional description.
3. Click "Choose File" under Photo and pick a picture — no coding needed.
4. Click **ADD TO STORE**. It appears on the live storefront immediately,
   and the photo itself is now stored safely on Cloudinary.

You can edit or delete any product from the same dashboard. Deleting a
product also removes its photo from Cloudinary, so you don't build up
unused files there over time.

## How checkout works

There's no payment gateway — items are priced in GHS for display only.
When a customer clicks **CHECKOUT ON WHATSAPP**, the site opens WhatsApp
with a message already typed out listing what they want to buy and the
total. They just hit send, and you take it from there.

## Deploying to Render

1. Push this folder to a GitHub repository (make sure `.env` is NOT
   included — `.gitignore` already prevents this, but double check on
   GitHub after pushing).
2. On Render: **New → Web Service** → connect your repo.
3. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. **Before deploying**, go to the **Environment** tab on Render and add
   these three variables (same names as in `.env.example`, with your
   real values):
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`
5. Deploy. Once live, log into `/admin/login` with your new credentials
   and add your real products — the photos will now persist across
   redeploys.

If anything errors during deploy, share the log and we can debug it.
