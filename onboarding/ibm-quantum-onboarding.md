# IBM Quantum Platform Onboarding Guide

This guide walks you through setting up access to IBM Quantum Platform with a free Open Plan instance.

> Last verified: October 2026. Screens may change over time.

> **Note:** Step 2 and later may be updated for the tutorial. If there are any changes, updates will be posted at https://github.com/qrmi-community/SC26 by November 9, 2026. Please check the site before the tutorial.

## Prerequisites

- An email address (or a Google / Red Hat account)
- A credit card for identity verification
  - You will not be charged as long as you use only the free Open Plan.

## Step 1: Create a trial IBM Cloud account

> **Already have an IBM Cloud account?** Skip this step and go to Step 2.

1. Go to https://quantum.cloud.ibm.com/registration.
2. On the **Create a trial IBM Cloud account** page, complete the following sections in order:
   1. **Account information**: Enter your email address and password, or sign up with Google or Red Hat.
   2. **Email verification**: Enter the verification code sent to your email.
   3. **Personal information**: Fill in your details.
   4. **Account notice**: Review and accept.
3. Enter your credit card information for identity verification when prompted.

> **Note:** The trial account expires after 30 days. After that, you need to upgrade to a Pay-As-You-Go account to keep using it. You will not be charged if you continue to use only the free Open Plan.

## Step 2: Log in to IBM Quantum Platform

1. Go to https://quantum.cloud.ibm.com/.
2. Log in with the account you created in Step 1.

## Step 3: Create your free Open Plan instance

On your first login, a **Create your free instance to get started** dialog appears.

1. Review the preset details:
   - **Instance name:** `open-instance`
   - **Region:** `us-east`
2. Select the checkbox **I have read and agree to the following license agreements**.
3. Click **Create instance**.

You are taken to the Open Plan dashboard.

### Verify: Check the available QPUs

On the dashboard, confirm that the **QPUs** panel shows **3** QPUs available to your Open Plan instance:

| QPU | Qubits | Region | Processor |
|---|---|---|---|
| `ibm_kingston` | 156 | us-east | Heron r2 |
| `ibm_fez` | 156 | us-east | Heron r2 |
| `ibm_marrakesh` | 156 | us-east | Heron r2 |

Click **View all** to see more details about each QPU.

> **Note:** The list of available QPUs may change over time as IBM adds or retires systems.

> **Note:** The Open Plan provides 10 minutes of QPU time for free. The dialog says "each month," but the official documentation defines it as 10 minutes per rolling 28-day window.

## Step 4: Create an API key and copy your instance CRN

These credentials are required to access IBM Quantum from Qiskit.

### Create an API key

1. In the **API key** section at the top left of the dashboard, click **Create**.
2. When the **API key successfully created** dialog appears, click **Copy** or **Download** and store the API key in a secure location.

> **Warning:** The API key is displayed only once and disappears after a short time. You cannot retrieve it later, so save it before closing the dialog.

### Copy your instance CRN

1. In the **Instances** section, just below the API key section, find `open-instance`.
2. Click the **CRN** copy icon next to it.
3. Store the CRN in a secure location.

> **Tip:** The Instances section also shows your plan (`open`) and remaining QPU time (for example, `10m 0s (100%) remain`).

> **Important:** Treat your API key like a password. Do not share it or commit it to public code repositories.

## Step 5: Choose a QPU for the tutorial

1. In the **QPUs** section of the dashboard, hover over each QPU name.
2. A tooltip shows the QPU's **Status** (for example, `Online`) and the number of **Pending jobs** currently in its queue.
3. Note the QPU with the fewest pending jobs. You will use this QPU in the tutorial.

## References

- [Set up your IBM Cloud account](https://quantum.cloud.ibm.com/docs/en/guides/cloud-setup)
- [Create and manage instances](https://quantum.cloud.ibm.com/docs/en/guides/instances)
- [Save your login credentials](https://quantum.cloud.ibm.com/docs/en/guides/save-credentials)
- [Support](https://quantum.cloud.ibm.com/docs/en/guides/support)
