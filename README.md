# **CalvinBot: A Comic-Posting Machine 🤖✨**

Ever wished Calvin and Hobbes comics would magically appear on your Bluesky feed? Well, CalvinBot's got you covered! This bot fetches, stores, and posts comics on autopilot—so you can enjoy a daily dose of Calvin's wisdom (or chaos) without lifting a finger.

## **What It Does 🚀**
- **📢 Posts Comics to Bluesky** – Because Calvin *needs* an audience.  
- **🎯 Smart Scheduling** – Uses AWS Lambda + EventBridge to keep things running smoothly.  
- **🗂️ Saves Comics in S3** – No lost comics, no worries.  
- **🤖 Auto-Fetching** – If there are unposted comics, it waits. If not, it fetches more.  

## **How It Works 🔄**
1. **Fetch Comics** – CalvinBot grabs comics and stores them in an S3 bucket.
2. **Check Unposted Comics** – If there are unposted ones, it waits. If not, it fetches more.
3. **Post to Bluesky** – Boom! Calvin & Hobbes appear like magic.

## **Tech Stack 🛠️**
- **AWS Lambda** – Runs the fetching and posting functions.
- **Amazon S3** – Stores fetched comics.
- **EventBridge** – Triggers the bot to run on schedule.
- **Bluesky API** – Posts comics automatically.

4. **Enjoy the comics! 🎉**

## **Want to Tweak It?**
- Modify the schedule? Adjust the AWS EventBridge timing.
- Add custom captions? Go wild.
- Make CalvinBot self-aware? Maybe... don’t. 😆

---

CalvinBot is here to keep your feed fun. Enjoy the nostalgia, and let Calvin do the talking! 🏆

