# Quick Start Guide - Arbitrage Analyzer

## Two Ways to Analyze Items

### Option 1: Single Item Checker (Quick & Easy)

Perfect for quick checks when you find an individual item and want to evaluate it immediately.

#### Steps:
1. Open the app at your deployment URL
2. Click the **"Check Single Item"** button in the header
3. Fill in the item details:
   - **Title** (required): Full item name/description
   - **MSRP** (required): Manufacturer's suggested retail price
   - **Item Number** (optional): SKU, Model #, or Part #
   - **Quantity** (optional): Number of units (default: 1)
   - **Notes** (optional): Condition, location, etc.
4. Click **"Analyze Item"**
5. Review the results:
   - Estimated sale price
   - Suggested purchase price (30% rule)
   - Profit per item
   - Demand level (High/Medium/Low)
   - Estimated sales time
   - AI reasoning
   - Total calculations (for quantities > 1)

#### Example Use Case:
You find a Milwaukee power drill at an estate sale marked $75. The original MSRP is $199.99. 
- Enter the details
- AI suggests you could sell it for ~$130
- Recommended purchase price: $39 (30% of sale price)
- Since it's $75, you can see if it's worth buying

---

### Option 2: CSV Manifest Upload (Bulk Analysis)

Best for liquidation pallets and manifests with many items.

#### Steps:
1. Open the app at your deployment URL
2. Optionally name your analysis (e.g., "Staples Pallet Jan 2025")
3. Choose upload method:
   - **Upload File**: Drag & drop or click to select CSV
   - **Paste CSV Data**: Copy/paste CSV content
4. Click **"Analyze Manifest"**
5. Wait for processing (progress bar shows real-time status)
6. Review detailed results:
   - Summary statistics
   - Item-by-item breakdown
   - Charts and visualizations
   - Profitability analysis

#### Supported CSV Formats:
- Grainger manifests
- Liquidation.com
- Wayfair liquidation
- Staples
- DirectLiquidation
- Most generic product manifests

---

## Understanding the Results

### Single Item Results

**Estimated Sale Price**: What you can realistically sell the item for (typically 40-65% of MSRP for liquidation items)

**Purchase Price**: Suggested maximum you should pay (30% of estimated sale price)

**Profit Per Item**: Sale price minus purchase price

**Demand Level**:
- 🟢 **High**: Fast-moving items, likely to sell quickly
- 🟡 **Medium**: Moderate demand, may take a few months
- 🔴 **Low**: Slower-moving, niche market

**Sales Time**: Estimated time to sell based on market analysis

**ROI**: Return on investment percentage
- Formula: (Profit / Purchase Price) × 100
- Example: Buy for $30, sell for $100, profit $70 = 233% ROI

### Total Summary (Bulk Quantities)

When analyzing multiple units, you'll see:
- **Total Investment**: How much to spend on all units
- **Total Revenue**: Expected sales from all units
- **Total Profit**: Net profit after costs
- **ROI**: Overall return percentage

---

## Pricing Model

The analyzer uses a **liquidation purchase model**:

1. **Estimated Sale Price**: 40-65% of MSRP (varies by item type and demand)
2. **Purchase Price**: 30% of estimated sale price
3. **Your Cost Basis**: 12-20% of MSRP typically

This model assumes:
- Buying through liquidation channels at steep discounts
- Selling on eBay, Amazon, or local marketplaces
- Standard marketplace fees and shipping costs

### Example:
- Item MSRP: $500
- Estimated Sale Price: $275 (55% of MSRP)
- Suggested Purchase Price: $82.50 (30% of sale price)
- Your Profit: $192.50 per unit
- ROI: 233%

If you can buy for less than $82.50, even better!

---

## Tips for Best Results

### For Single Item Checks:
1. **Use accurate MSRP**: Check manufacturer website for official retail price
2. **Be specific in title**: Include brand, model, size, etc.
3. **Add notes**: Condition affects value (new, used, refurbished)
4. **Check quantity pricing**: Bulk purchases may offer better deals

### For CSV Manifests:
1. **Clean your data**: Remove duplicate headers or empty rows
2. **Name your upload**: Makes it easy to find later in history
3. **Review all items**: Sort by profit to find the best deals
4. **Use filters**: Focus on high-demand, profitable items

---

## Common Questions

**Q: How accurate is the AI analysis?**
A: The AI provides educated estimates based on market trends, but actual prices vary by condition, timing, and marketplace. Use it as a guide, not a guarantee.

**Q: Can I save single item checks?**
A: Currently, single item checks are not saved to your history. They're designed for quick, on-the-fly analysis.

**Q: What if my CSV format isn't supported?**
A: The parser is flexible and attempts to find common columns (title, price, item number). Most formats work, but you may need to clean the data first.

**Q: Can I export results?**
A: Export functionality is planned for a future update. For now, you can copy data from the results table.

**Q: How long does processing take?**
A: Single items: 2-5 seconds. CSV manifests: 1-3 minutes for 50-100 items, depending on AI analysis load.

---

## Navigation

- **Check Single Item** button: Switch to single item mode
- **View History**: See your past CSV uploads
- **Back buttons**: Return to main upload screen
- **Reset/Check Another**: Clear form and start fresh

---

## Getting Help

If you encounter issues:
1. Check that all required fields are filled
2. Verify your CSV format is correct
3. Clear browser cache and try again
4. Contact support with error messages

---

## Quick Reference

| Feature | Best For | Time | Saves to History |
|---------|----------|------|------------------|
| Single Item | Quick checks, individual finds | 2-5 sec | No |
| CSV Upload | Liquidation pallets, bulk manifests | 1-3 min | Yes |

---

Happy analyzing! 🚀

