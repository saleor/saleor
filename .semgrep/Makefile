test:
	semgrep --test ./

scan:
	semgrep scan \
		--metrics=off \  # Disable Telemetry
		--disable-version-check \
		--no-rewrite-rule-ids \  # Don't put directory name in the rule IDs
		--error \  # Exit with error code 1 if there are finding
		-c rules/ \
		../
