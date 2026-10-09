"""
Sample Marketing Documents for Testing

These documents simulate various marketing records that the processor should handle.
"""

SAMPLE_DOCUMENTS = [
    # Campaign briefs
    """
    CAMPAIGN BRIEF

    Date: 2024-01-10

    Campaign: Spring Product Launch

    This campaign will drive awareness for the v3 launch through our
    Email channel. The approved budget is $150,000, with a launch
    date of 2024-01-15.

    Please send creative assets for review by 2024-01-12.

    Best regards,
    Marketing Team
    """,

    """
    CAMPAIGN BRIEF

    Date: 2024-01-18

    Campaign: Webinar Series

    We are excited to kick off a webinar series run through our
    Content channel. The program has an approved budget of
    $140,000 for the quarter.

    The first session launches on 2024-02-01.

    Thanks!
    Demand Gen Team
    """,

    """
    CREATIVE BRIEF

    Campaign: Retargeting Push
    Owner: Growth Marketing
    Channel: Paid Social
    Budget: $145,000
    Launch Date: 2024-01-20

    Final creative is contingent upon brand team approval.
    """,

    # Budget change
    """
    BUDGET CHANGE NOTICE

    Campaign: Partner Co-Marketing
    Current Budget: $120,000
    New Budget: $160,000
    Channel: Events
    Effective Date: 2024-02-01

    Approved by the VP of Marketing following strong Q4 results.
    """,

    # Another brief
    """
    CAMPAIGN BRIEF

    Campaign: SEO Content Refresh
    Channel: Content
    Budget: $120,000
    Launch: 2024-03-01

    We look forward to refreshing our top-performing blog posts.
    """,
]

# Larger batch for stress testing
LARGE_BATCH = SAMPLE_DOCUMENTS * 10  # 50 documents
