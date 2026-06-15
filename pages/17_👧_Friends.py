import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from category_page import render_category_page

render_category_page("Friends", "frnd", "👧", "LEGO Friends minifigures (frnd####)")
