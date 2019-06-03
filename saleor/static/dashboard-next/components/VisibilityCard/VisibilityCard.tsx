import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as moment from "moment-timezone";
import * as React from "react";

import CardTitle from "../../components/CardTitle";
import ControlledSwitch from "../../components/ControlledSwitch";
import FormSpacer from "../../components/FormSpacer";
import { LocaleConsumer } from "../../components/Locale";
import i18n from "../../i18n";

export interface FormData {
  isPublished: boolean;
  publicationDate: string;
}

export interface VisibilityCardProps {
  data: FormData;
  disabled: boolean;
  errors: Partial<Record<"publicationDate", string>>;
  onChange: (event: React.ChangeEvent<any>, cb?: () => void) => void;
}

const VisibilityCard: React.StatelessComponent<VisibilityCardProps> = ({
  data,
  disabled,
  errors,
  onChange
}) => (
  <LocaleConsumer>
    {locale => (
      <Card>
        <CardTitle title={i18n.t("Visibility")} />
        <CardContent>
          <ControlledSwitch
            checked={
              (data.publicationDate === "" || data.publicationDate === null) &&
              data.isPublished
            }
            disabled={disabled}
            label={
              data.isPublished && !data.publicationDate ? (
                i18n.t("Visible")
              ) : (
                <>
                  {i18n.t("Hidden")}
                  {data.publicationDate && (
                    <Typography variant="caption">
                      {i18n.t("Will become visible on {{ date }}", {
                        context: "page",
                        date: moment(data.publicationDate)
                          .locale(locale)
                          .format("ll")
                      })}
                    </Typography>
                  )}
                </>
              )
            }
            name={"isPublished" as keyof FormData}
            onChange={event =>
              onChange(
                event,
                () =>
                  event.target.value &&
                  onChange({
                    target: {
                      name: "publicationDate",
                      value: ""
                    }
                  } as any)
              )
            }
          />
          {!(data.publicationDate === "" || data.publicationDate === null) &&
            data.isPublished && (
              <>
                <FormSpacer />
                <TextField
                  disabled={disabled}
                  error={!!errors.publicationDate}
                  fullWidth
                  helperText={errors.publicationDate}
                  label={i18n.t("Publish on")}
                  name={"publicationDate" as keyof FormData}
                  type="date"
                  value={data.publicationDate}
                  onChange={onChange}
                />
              </>
            )}
        </CardContent>
      </Card>
    )}
  </LocaleConsumer>
);
VisibilityCard.displayName = "VisibilityCard";
export default VisibilityCard;
