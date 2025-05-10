# CITS3403 Group Project
2025 Agile Web Development Project

## Purpose
This web application is a trade journal designed for day traders. The primary focus of trading is not just on the strategies or techniques but also on the psychology behind the trades. Trading is said to be 10% about how to trade and 90% about controlling your emotions. The profitability of a trader largely depends on their emotional discipline and ability to learn from their experiences.

The key motto is: *"You don’t lose until you give up."* A loss, when following your plan, is seen as part of your strategy’s edge. However, it only holds value if you learn from it. 

Journaling plays a crucial role in a trader's success. This app allows traders to upload their profits and attach up to 5 images of their trades. This helps them review their actions objectively, outside the emotional context of the trade. Additionally, the journal reinforces better habits and builds confidence by reinforcing positive outcomes and identifying areas of improvement.

The journal allows users to track emotions and assess whether they followed their own set rules using a tag system. The trade journal not only helps refine strategies and adapt to different market conditions but also builds the confidence to make better trading decisions, including managing trade size based on previous experiences.

# Setup

*These instructions are targeted towards Linux. On Windows, simply substitute `python3` for `py`.*

First, create a Python virtual environment and source it:

```bash
python3 -m venv application-env
source application-env/bin/activate
```

Install required packages:

```bash
pip install -r requirements.txt
```

Run the server:

```bash
python3 main.py
```
