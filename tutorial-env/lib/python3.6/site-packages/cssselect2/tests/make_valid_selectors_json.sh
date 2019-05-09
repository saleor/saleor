#!/bin/sh

WEB_PLATFORM_TESTS="$1"

if [ -f "$WEB_PLATFORM_TESTS/selectors-api/selectors.js" ]
then
    (
        cat "$WEB_PLATFORM_TESTS/selectors-api/selectors.js"
        echo "validSelectors.map(function(selector) {"
        echo "   delete selector.testType;"
        echo "});"
        echo "console.log(JSON.stringify(validSelectors, null, '  '))"
    ) | node
else
    echo "Usage: $0 path/to/web-plateform-test"
    exit;
fi
