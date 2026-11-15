# IBM Quantum Platform Onboarding Guide

This guide walks you through setting up access to the IBM Quantum instance provided for the SC26 TUT171 tutorial.

> Last verified: November 15, 2026. Screens may change over time.

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

## Step 2: Request access to the IBM Quantum instance for the tutorial

1. Go to https://forms.cloud.microsoft/r/XgeLVrkb7u and submit the form.
2. You will receive an email invitation to the instance at your registered email address. Click the "Join now" link in the email.

## Step 3: Log in to IBM Quantum Platform

1. Go to https://quantum.cloud.ibm.com/.
2. Log in with the account you used in Step 1 (email, Google, or Red Hat).
3. From the account switcher in the top header, select "3115573 - itz-saas-174".
4. From the region switcher next to it, select **us-east**.

> **Note:** If you don't see "3115573 - itz-saas-174" in the account switcher, make sure you have accepted the invitation in Step 2.

### Verify: Check the available QPUs

On the dashboard, confirm that the **QPUs** panel shows **3** QPUs available to the **QRMI Demo** instance:

| QPU | Qubits | Region | Processor |
|---|---|---|---|
| `ibm_kingston` | 156 | us-east | Heron r2 |
| `ibm_fez` | 156 | us-east | Heron r2 |
| `ibm_marrakesh` | 156 | us-east | Heron r2 |

Click **View all** to see more details about each QPU.

> **Note:** The list of available QPUs may change over time as IBM adds or retires systems.

## Step 4: Create an API key and copy your instance CRN

These credentials are required to access IBM Quantum from Qiskit.

### Create an API key

> **Note:** Before you create the API key, make sure "3115573 - itz-saas-174" is selected in the account switcher.

1. In the **API key** section at the top left of the dashboard, click **Create**.
2. When the **API key successfully created** dialog appears, click **Copy** or **Download** and store the API key in a secure location.

> **Warning:** The API key is displayed only once and disappears after a short time. You cannot retrieve it later, so save it before closing the dialog.

### Copy your instance CRN

1. In the **Instances** section, just below the API key section, find `QRMI Demo`.
2. Click the **CRN** copy icon next to it.
3. Store the CRN in a secure location.

> **Tip:** The Instances section also shows the instance's plan (`flux`) and remaining resources (for example, `180.00 RU remain`).

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
