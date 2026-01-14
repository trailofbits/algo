#!/bin/bash
# Test all Jinja2 templates in the Algo codebase
# This script is called by CI and can be run locally

set -e

echo "======================================"
echo "Running Jinja2 Template Tests"
echo "======================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# 1. Run the template syntax validator
echo "1. Validating Jinja2 template syntax..."
echo "----------------------------------------"
if python tests/validate_jinja2_templates.py; then
    echo -e "${GREEN}✓ Template syntax validation passed${NC}"
else
    echo -e "${RED}✗ Template syntax validation failed${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# 2. Run the template rendering tests
echo "2. Testing template rendering..."
echo "--------------------------------"
if python tests/unit/test_template_rendering.py; then
    echo -e "${GREEN}✓ Template rendering tests passed${NC}"
else
    echo -e "${RED}✗ Template rendering tests failed${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# 3. Run the StrongSwan template tests
echo "3. Testing StrongSwan templates..."
echo "----------------------------------"
if python tests/unit/test_strongswan_templates.py; then
    echo -e "${GREEN}✓ StrongSwan template tests passed${NC}"
else
    echo -e "${RED}✗ StrongSwan template tests failed${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# 4. Run ansible-lint with Jinja2 checks enabled
echo "4. Running ansible-lint Jinja2 checks..."
echo "----------------------------------------"
# Check only for jinja[invalid] errors, not spacing warnings
if ansible-lint --nocolor 2>&1 | grep -E "jinja\[invalid\]"; then
    echo -e "${RED}✗ ansible-lint found Jinja2 syntax errors${NC}"
    ansible-lint --nocolor 2>&1 | grep -E "jinja\[invalid\]" | head -10
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✓ No Jinja2 syntax errors found${NC}"
    # Show spacing warnings as info only
    if ansible-lint --nocolor 2>&1 | grep -E "jinja\[spacing\]" | head -1 > /dev/null; then
        echo -e "${YELLOW}ℹ Note: Some spacing style issues exist (not failures)${NC}"
    fi
fi
echo ""

# Summary
echo "======================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All template tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$FAILED test suite(s) failed${NC}"
    echo ""
    echo "To debug failures, run individually:"
    echo "  python tests/validate_jinja2_templates.py"
    echo "  python tests/unit/test_template_rendering.py"
    echo "  python tests/unit/test_strongswan_templates.py"
    echo "  ansible-lint"
    exit 1
fi
