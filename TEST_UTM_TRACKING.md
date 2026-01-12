# UTM Tracking - Quick Test Guide

> **Status**: Migration applied ✅, Code deployed ✅
> **Date**: 2026-01-12

---

## Quick Test (5 minutes)

### Step 1: Test Attribution Capture

Open your browser and visit:
```
http://localhost:3000/series/villainess-survives?utm_source=test&utm_campaign=manual-test&utm_medium=debug
```

**Verify**:
1. Open DevTools → Application → Local Storage
2. Look for key: `signup_attribution`
3. Should contain:
```json
{
  "source": "test",
  "campaign": "manual-test",
  "medium": "debug",
  "content": null,
  "landingPage": "/series/villainess-survives",
  "referrer": "..."
}
```

✅ If you see this, attribution capture is working!

---

### Step 2: Test Attribution Saving

**Sign up with a new test email:**
1. Click "Start Episode 0" on the series page
2. Sign up with `your-email+test-utm@gmail.com`
3. Complete auth flow
4. You should land in the episode chat

**Verify in database:**
```bash
export FANTAZY_DB_PASSWORD='42PJb25YJhJHJdkl'

PGPASSWORD="$FANTAZY_DB_PASSWORD" psql \
  "postgresql://postgres.lfwhdzwbikyzalpbwfnd@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres" \
  -c "SELECT display_name, signup_source, signup_campaign, signup_medium, signup_landing_page FROM users ORDER BY created_at DESC LIMIT 1;"
```

**Expected output:**
```
 display_name | signup_source | signup_campaign | signup_medium | signup_landing_page
--------------+---------------+-----------------+---------------+---------------------
 Test User    | test          | manual-test     | debug         | /series/villainess-survives
```

✅ If you see this, attribution is being saved!

---

### Step 3: Test Admin Dashboard

1. Go to `http://localhost:3000/admin`
2. Scroll to "User Engagement" table
3. Look for your test user

**Should see:**
- Source: `test`
- Campaign: `manual-test`

**Scroll to "Campaign Performance" card:**

Should show:
```
Source    Campaign        Signups  Activated  Rate
test      manual-test     1        0          0%
```

(Rate is 0% because you haven't sent a message yet)

✅ If you see this, admin dashboard is working!

---

### Step 4: Test Activation Tracking

**Send a test message:**
1. In the episode chat, click a choice or type a message
2. Send at least one message

**Refresh admin dashboard:**

Campaign Performance should now show:
```
Source    Campaign        Signups  Activated  Rate
test      manual-test     1        1          100%   ← Changed!
```

✅ If rate changed to 100%, activation tracking works!

---

## Production Test

### Update One Real Ad

**Pick your best performing Reddit ad**, add UTM:

**Before:**
```
URL: ep-0.com/series/villainess-survives
```

**After:**
```
URL: ep-0.com/series/villainess-survives?utm_source=reddit&utm_campaign=oi-villainess-test&utm_medium=cpc
```

**Wait 24 hours**, then check `/admin`:

You should see signups with:
- Source: `reddit`
- Campaign: `oi-villainess-test`

And you'll be able to see the activation rate for that specific campaign.

---

## Expected Results After 1 Week

With all ads updated to include UTM parameters, you should see:

```
Campaign Performance:

Source    Campaign                  Signups  Activated  Activation %
reddit    oi-villainess-v2-chat    8        3          37%
reddit    manhwa-regressor-v2      5        2          40%
tiktok    oi-villainess-jan        12       1          8%
unknown   -                        15       0          0%
```

**Analysis:**
- ✅ Reddit campaigns are working (37-40% activation)
- ⚠️ TikTok needs work (8% activation)
- ❌ "unknown" users = people who came directly or from old ads without UTM

**Action:**
- Stop TikTok campaign or revise targeting
- Add UTM to remaining ads to reduce "unknown" signups
- Increase budget on Reddit campaigns

---

## Troubleshooting

### LocalStorage is empty
- Check browser console for errors
- Make sure you visited the page with `?utm_source=...` in URL
- Try clearing cache and visiting again

### Attribution not in database
- Check that `AttributionSaver` component is running
- Open browser console, look for any errors
- Verify you're authenticated (logged in)

### Admin dashboard shows "unknown"
- This is normal for:
  - Old users (signed up before today)
  - Users who didn't come from UTM links
  - Direct traffic (typed URL)

### "Tenant or user not found" (database)
- Check you're using correct password
- Make sure using `aws-1-ap-northeast-1` pooler

---

## Next Steps

After confirming it works:

1. **Update ALL ad URLs** with UTM parameters
   - Use the templates in `docs/marketing/REDDIT_ADS_REVISED_COPY.md`

2. **Monitor for 3-7 days**
   - Check admin dashboard daily
   - Look for which campaigns activate users

3. **Optimize spend**
   - Stop campaigns with 0% activation
   - Double budget on campaigns with >30% activation

4. **A/B test**
   - Test "Play Now" vs "Start Chat" CTAs
   - Use different `utm_campaign` values to track each variant

---

## Success Criteria

✅ Attribution captured in localStorage
✅ Attribution saved to database
✅ Admin dashboard shows source/campaign
✅ Campaign performance card calculates activation rates
✅ Can compare different campaigns

**YOU'RE DONE!** 🎉

Now you have full visibility into which campaigns work.
