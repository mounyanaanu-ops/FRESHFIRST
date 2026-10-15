# FRESHFIRST
# FreshFirst

### Explainable Perishable Inventory Planning & Dispatch Optimization

FreshFirst is a decision-support platform for perishable inventory planning. It helps businesses make smarter dispatch decisions by prioritizing inventory based on remaining shelf life while considering destination demand, transportation time, delivery feasibility, and available capacity.

The goal is simple:

> **Dispatch what is most at risk first — while making sure the destination can actually receive and sell it.**

---

## 🚨 Problem

Perishable inventory has a limited selling window. Poor dispatch decisions can result in:

- Inventory expiring before it reaches a destination
- Avoidable food waste and spoilage
- Unfulfilled customer demand
- Inefficient use of transportation capacity
- Revenue loss from unsold inventory

Traditional inventory allocation approaches may focus mainly on availability or demand without sufficiently considering remaining shelf life and transportation feasibility.

FreshFirst addresses this by combining perishability, demand, capacity, and delivery constraints into an explainable planning process.

---

## 💡 Solution

FreshFirst generates batch-to-destination dispatch recommendations using a rule-based planning approach.

The planning engine considers:

- Remaining shelf life
- Inventory quantity
- Destination demand
- Destination capacity
- Transportation time
- Delivery feasibility
- Inventory urgency
- Potential revenue
- At-risk inventory

The system also identifies inventory that may be difficult to sell before expiry and recommends discount actions where appropriate.

---

## ⚙️ How It Works

```text
Inventory + Demand + Transport + Capacity
                    ↓
          Feasibility Analysis
                    ↓
        Perishability-Aware Planning
                    ↓
          Dispatch Recommendations
                    ↓
       At-Risk Inventory Detection
                    ↓
         Discount Recommendations
                    ↓
       Baseline Performance Comparison
