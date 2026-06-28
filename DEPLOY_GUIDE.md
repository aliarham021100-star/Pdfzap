# BizTrack — Deployment & Earning Guide

## 🚀 Local Run
```bash
pip install -r requirements.txt
python app.py
# Open: http://localhost:5004
```

---

## 🌐 Public Deploy (Free Hosting)

### Option 1 — PythonAnywhere (Recommended)
1. https://www.pythonanywhere.com — free account
2. Files upload karein
3. Web app setup karein (Flask)
4. Free subdomain milega: yourname.pythonanywhere.com

### Option 2 — Render.com
1. https://render.com — free tier
2. GitHub pe code upload karein
3. New Web Service banayein
4. Automatic deploy hoga

### Option 3 — Railway.app
1. https://railway.app
2. GitHub se connect karein
3. Deploy karein

---

## 💰 Earning Setup

### 1. Google AdSense
1. https://adsense.google.com pe apply karein
2. Website approve hone ke baad publisher ID milega
3. index.html mein yeh uncomment karein:
   ```html
   <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-APKA_ID"></script>
   ```
4. Ad units banayein aur HTML mein daalen

### 2. Premium Plan (Stripe)
1. https://stripe.com — free account
2. Payment link banayein ($9.99/month)
3. upgradePlan() function mein Stripe checkout add karein:
   ```javascript
   window.location.href = 'https://buy.stripe.com/YOUR_LINK';
   ```

### 3. Revenue Estimate
- 1000 daily users = ~$3-8/day AdSense
- 50 premium users = $500/month
- Combined: $600-800/month potential

---

## 📈 SEO Tips
- Domain lein: biztrack.com (~$10/year)
- Google Search Console mein submit karein
- Keywords: "free invoice generator", "expense tracker online"
