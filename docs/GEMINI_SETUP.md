# 🆓 Using FREE Gemini API Instead of OpenAI

## Why Gemini?

✅ **Completely FREE** - No credit card required  
✅ **Generous limits** - 15 requests/minute, 1500/day  
✅ **Powerful** - Gemini 1.5 Flash is fast and capable  
✅ **Easy setup** - Get API key in 2 minutes  

Perfect for testing and small projects!

## Step 1: Get Your FREE Gemini API Key (2 minutes)

1. **Go to Google AI Studio**  
   Visit: https://aistudio.google.com/app/apikey

2. **Sign in with Google**  
   Use any Google account (Gmail, etc.)

3. **Create API Key**  
   - Click **"Get API key"** or **"Create API key"**
   - Select **"Create API key in new project"**
   - Copy the key (starts with `AIza...`)

4. **Done!** No credit card, no billing setup needed!

## Step 2: Install Gemini SDK

```powershell
pip install google-generativeai
```

## Step 3: Update .env File

Open `.env` and update these lines:

```bash
# Choose Gemini as provider
LLM_PROVIDER=gemini

# Add your Gemini API key
GEMINI_API_KEY=AIzaSyABC123def456GHI789jkl012MNO345pqr

# Choose model (flash is faster, pro is more capable - both FREE!)
GEMINI_MODEL=gemini-1.5-flash

# Keep these for GitHub integration
GITHUB_TOKEN=ghp_your-token-here
GITHUB_WEBHOOK_SECRET=my-secret-123
WEBHOOK_ALLOW_UNSIGNED=true
```

## Step 4: Test It!

```powershell
# Test configuration
python -c "from devsecops_agent.settings import get_settings; s = get_settings(); print(f'✅ Using {s.llm_provider} with model {s.get_model_name()}')"

# Should output:
# ✅ Using gemini with model gemini-1.5-flash
```

## Step 5: Start the Agent

```powershell
python -m devsecops_agent.webhook.serve
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8080
```

## Step 6: Test with a Diff (CLI Mode)

```powershell
# Create a test diff
echo "query = f'SELECT * FROM users WHERE id={user_id}'" > test.py
git add test.py
git diff --cached > test.diff

# Review it with Gemini
python -m devsecops_agent --diff test.diff -l python

# You'll see a security review powered by Gemini!
```

## Step 7: Test with GitHub Webhook

Follow the same steps as before:

1. **Start ngrok**: `ngrok http 8080`
2. **Configure GitHub webhook** with ngrok URL
3. **Create test PR** with vulnerable code
4. **Watch Gemini review it automatically!** 🎉

## Gemini vs OpenAI

| Feature | Gemini (FREE) | OpenAI (Paid) |
|---------|---------------|---------------|
| **Cost** | 🆓 FREE | 💰 $0.15-$10 per 1M tokens |
| **Setup** | No credit card | Credit card required |
| **Rate Limit** | 15 req/min | Varies by tier |
| **Daily Limit** | 1500 requests | Based on credits |
| **Quality** | Excellent | Excellent |
| **Speed** | Fast (Flash) | Fast (4o-mini) |

## Gemini Models

### gemini-1.5-flash (Recommended)
- **Speed**: Very fast
- **Cost**: FREE
- **Best for**: Most use cases, testing
- **Context**: 1M tokens

### gemini-1.5-pro
- **Speed**: Slower but more capable
- **Cost**: FREE
- **Best for**: Complex analysis
- **Context**: 2M tokens

To switch models, update `.env`:
```bash
GEMINI_MODEL=gemini-1.5-pro
```

## Troubleshooting

### "GEMINI_API_KEY is required"

**Fix**: Make sure `.env` has:
```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIza...your-key-here
```

### "google-generativeai not installed"

**Fix**: Install the package:
```powershell
pip install google-generativeai
```

### "API key not valid"

**Fix**: 
1. Check your key at https://aistudio.google.com/app/apikey
2. Make sure you copied the full key (starts with `AIza`)
3. No spaces or quotes around the key in `.env`

### Rate limit exceeded

**Fix**: Gemini free tier allows 15 requests/minute
- Wait a minute and try again
- Or upgrade to paid tier (very affordable)

## Switching Between Providers

You can easily switch between Gemini and OpenAI:

### Use Gemini (FREE)
```bash
# In .env
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIza...
```

### Use OpenAI (Paid)
```bash
# In .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

Just change `LLM_PROVIDER` and restart the agent!

## Cost Comparison

### For 1000 PR Reviews (average 500 lines each):

**Using Gemini:**
- Cost: **$0.00** (FREE!)
- Time: ~30 seconds per review
- Total: FREE

**Using OpenAI (gpt-4o-mini):**
- Cost: ~$2.00
- Time: ~20 seconds per review
- Total: $2.00

**Using OpenAI (gpt-4o):**
- Cost: ~$20.00
- Time: ~25 seconds per review
- Total: $20.00

## Example Review Output

Gemini produces high-quality security reviews:

```markdown
### Summary
This PR introduces a critical SQL injection vulnerability in the authentication 
module. The code directly concatenates user input into SQL queries without 
parameterization.

### Critical Issues

**SQL Injection in login function**
- **Location**: test.py, line 1
- **Issue**: User input is directly interpolated into SQL query
- **Risk**: Attackers can execute arbitrary SQL commands
- **Fix**: Use parameterized queries:
  ```python
  query = "SELECT * FROM users WHERE id = %s"
  cursor.execute(query, (user_id,))
  ```
```

## Next Steps

1. ✅ Get Gemini API key (FREE!)
2. ✅ Update `.env` with `LLM_PROVIDER=gemini`
3. ✅ Test with CLI mode
4. ✅ Test with GitHub webhook
5. ✅ Enjoy FREE AI-powered security reviews!

## Resources

- **Get API Key**: https://aistudio.google.com/app/apikey
- **Gemini Docs**: https://ai.google.dev/docs
- **Pricing**: https://ai.google.dev/pricing
- **Rate Limits**: https://ai.google.dev/gemini-api/docs/quota

## Support

**Questions?** 
- Check [LOCAL_SETUP_STEPS.md](LOCAL_SETUP_STEPS.md)
- Open a GitHub issue
- Check Gemini docs

---

**🎉 Enjoy your FREE AI-powered security reviews with Gemini!**
