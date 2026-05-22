"""CSS used to soften the Streamlit default layout."""

DASHBOARD_CSS = """
<style>
.block-container {
    padding-top: 2rem;
}

[data-testid="stMarkdownContainer"] p {
    line-height: 1.45;
}

.story-placeholder {
    align-items: center;
    aspect-ratio: 16 / 10;
    background: #f3f5f7;
    border: 1px solid #e4e8ed;
    border-radius: 6px;
    color: #8a94a3;
    display: flex;
    font-size: 0.8rem;
    justify-content: center;
    width: 100%;
}
</style>
"""
