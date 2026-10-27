# Pasqal Cloud Onboarding Guide

This guide walks you through creating a free Pasqal Cloud account for the
tutorial's Pasqal exercises, which run on the `EMU_FREE` emulator.

> Last verified: October 2026. Screens may change over time.

> **Note:** If there are any changes for the tutorial, updates will be posted at https://github.com/qrmi-community/SC26 by November 9, 2026. Please check the site before the tutorial.

Do this at least a day before the session, so that email confirmation is not on
the critical path. If you cannot use Pasqal Cloud, every Pasqal exercise also
runs on the tutorial's local Warden backup, which needs no account.

## Prerequisites

- An email address

No contract or payment is needed: the free Explorer offer includes `EMU_FREE`.

## Step 1: Create your account

1. Go to the [Pasqal User Portal](https://portal.pasqal.cloud/) and sign up.
2. Confirm your email address with the link Pasqal sends you.

See Pasqal's [setup guide](https://docs.pasqal.com/cloud/set-up/) for details.

## Step 2: Log in and note your project ID

1. Log in to the [Pasqal User Portal](https://portal.pasqal.cloud/) once.
2. Accept any pending project invitation.
3. Open **Projects** in the portal's navigation bar and note the ID of the
   project you will use.

If no project is listed, ask the instructor before the session; the exercises
need a project ID.

## Step 3: Write your credentials file

During the hands-on you write your username, password and project ID to
`~/.pasqal/config` inside your tutorial container, with mode 600. Your
workload manager's Module 1 guide says in which container and as which user.
Run these commands there. They prompt for each value, and the password is not
echoed or saved in your shell history:

```bash
mkdir -p ~/.pasqal && chmod 700 ~/.pasqal
read -rp 'Pasqal Cloud username: ' pasqal_user
read -rsp 'Pasqal Cloud password: ' pasqal_password; echo
read -rp 'Pasqal project ID: ' pasqal_project
(umask 077; printf 'username=%s\npassword=%s\nproject_id=%s\n' \
  "$pasqal_user" "$pasqal_password" "$pasqal_project" > ~/.pasqal/config)
unset pasqal_password
ls -l ~/.pasqal/config
```

The listing should start with `-rw-------`. The file then contains:

```
username=<your Pasqal Cloud username>
password=<your Pasqal Cloud password>
project_id=<your project ID>
```

Instead of `username` and `password`, the file can hold `token=<your token>`
if you have a Pasqal Cloud access token.

> **Important:** Treat your password like any other secret. Never put it in the tutorial source, in shared files, in help reports or in public code repositories.

## References

- [Pasqal User Portal](https://portal.pasqal.cloud/)
- [Pasqal Cloud setup guide](https://docs.pasqal.com/cloud/set-up/)
