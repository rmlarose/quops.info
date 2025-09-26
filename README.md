# Project Setup and Usage Guide

## How to Run App Locally

1. Install **VS Code** or a code editor of your choice.  
2. Clone the git repo at your desired location:

   ```bash
   git clone https://github.com/rmlarose/quops.info.git
   ```

3. Open the project in VS Code:  
   `File > Open Folder > (open the project folder)`

4. Open a new terminal in VS Code:  
   `Terminal > New Terminal`

5. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Run the app:

   ```bash
   streamlit run app.py
   ```

⚠️ **Note**: The app is connected to an **AWS PostgreSQL database**.

---

## How to SSH into AWS and Pull Git Changes

1. Open any terminal on your local machine.  
2. Navigate to the directory containing `streamlit-key.pem`.  
3. Ensure correct permissions:

   ```bash
   chmod 400 streamlit-key.pem
   ```

4. SSH into the server:

   ```bash
   ssh -i "streamlit-key.pem" ubuntu@our_ip_address
   ```

5. Once inside the Ubuntu server:

   ```bash
   cd quops.info
   git pull origin master
   ```

⚠️ **Note**: Running `git pull` manually is not required if **GitHub Actions workflow** is set up. Pushing changes locally will automatically reflect on the AWS server.

---

## How to View and Interact with Database on AWS

⚠️ **Note**: This step is not required if **pgAdmin** is installed locally. You can directly view AWS tables and run queries there.

1. Follow **steps 1–5** from SSH instructions above.  
2. Enter the PostgreSQL shell:

   ```bash
   psql -U qcuser -d quants -h localhost
   ```

   (Enter your password when prompted)

3. You are now inside the psql shell (you might see `#quants`).  

4. Run queries, for example:

   ```sql
   SELECT * FROM quant_data;
   ```

   This will display the table contents.  

💡 To view other tables or filter rows, simply use the table name and columns let ChatGPT help generate **PostgreSQL queries** for your conditions (e.g., filter only Google-related computers).



---

## How to Install pgAdmin on Chromebook

▶️ Video guide: [How to install pgAdmin on Chromebook](https://www.youtube.com/watch?v=qdaCDKQN05w)

---

## After Installing pgAdmin

1. Open **pgAdmin**.  
2. Right-click on **Servers** → **Register > Server**.  
3. In the dialog box:  
   - **Name**: Give your server a name (e.g., `AWS_db`).  
   - Go to the **Connection** tab:  
     - **Host name/address**: your AWS IP  
     - **Maintenance database**: `quants`  
     - **Username**: `qcuser`  
     - **Password**: `our_password`  
   - Click **Save**.  

4. You are now connected to the database.  
5. Double-click `quants` → expand **Schemas > Tables** to view tables.  
6. To query data:  
   - Select `quants` DB → **Tools > Query Tool**.  
   - Close scratch pad.  
   - Type your query, e.g.:

     ```sql
     SELECT * FROM quant_data;
     ```

   - Click **Execute Query**. ✅

---
