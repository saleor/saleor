import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as moment from "moment-timezone";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import ControlledSwitch from "../../../components/ControlledSwitch";
import FormSpacer from "../../../components/FormSpacer";
import { LocaleConsumer } from "../../../components/Locale";
import i18n from "../../../i18n";
import { FormData } from "../PageDetailsPage";

export interface PageAvailabilityProps {
  data: FormData;
  disabled: boolean;
  errors: Partial<Record<"availableOn", string>>;
  onChange: (event: React.ChangeEvent<any>, cb?: () => void) => void;
}

function isAvailable(data: FormData): boolean {
  return (
    (data.availableOn === "" || data.availableOn === null) && data.isVisible
  );
}

const PageAvailability: React.StatelessComponent<PageAvailabilityProps> = ({
  data,
  disabled,
  errors,
  onChange
}) => (
  <LocaleConsumer>
    {locale => (
      <Card>
        <CardTitle title={i18n.t("Availability")} />
        <CardContent>
          <ControlledSwitch
            checked={isAvailable(data)}
            disabled={disabled}
            label={
              data.isVisible && !data.availableOn ? (
                i18n.t("Published")
              ) : (
                <>
                  {i18n.t("Hidden")}
                  {data.availableOn && (
                    <Typography variant="caption">
                      {i18n.t("Will become visible on {{ date }}", {
                        context: "page",
                        date: moment(data.availableOn)
                          .locale(locale)
                          .format("ll")
                      })}
                    </Typography>
                  )}
                </>
              )
            }
            name={"isVisible" as keyof FormData}
            onChange={event =>
              onChange(
                event,
                () =>
                  event.target.value &&
                  onChange({
                    target: {
                      name: "availableOn",
                      value: ""
                    }
                  } as any)
              )
            }
          />
          {!isAvailable(data) && (
            <>
              <FormSpacer />
              <TextField
                disabled={disabled}
                error={!!errors.availableOn}
                fullWidth
                helperText={errors.availableOn}
                label={i18n.t("Publish page on")}
                name={"availableOn" as keyof FormData}
                type="date"
                value={data.availableOn}
                onChange={onChange}
              />
            </>
          )}
        </CardContent>
      </Card>
    )}
  </LocaleConsumer>
);
PageAvailability.displayName = "PageAvailability";
export default PageAvailability;
