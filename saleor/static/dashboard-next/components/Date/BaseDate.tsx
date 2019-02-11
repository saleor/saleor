import Tooltip from "@material-ui/core/Tooltip";
import * as moment from "moment-timezone";
import * as React from "react";
import ReactMoment from "react-moment";

import { LocaleConsumer } from "../Locale";
import { TimezoneConsumer } from "../Timezone";
import { Consumer } from "./DateContext";

interface BaseDateProps {
  date: string;
  format: string;
  plain?: boolean;
}

const BaseDate: React.StatelessComponent<BaseDateProps> = ({
  date,
  format,
  plain
}) => {
  const getTitle = (value: string, locale?: string, tz?: string) => {
    let date = moment(value).locale(locale);
    if (tz !== undefined) {
      date = date.tz(tz);
    }
    return date.format(format);
  };
  return (
    <LocaleConsumer>
      {locale => (
        <TimezoneConsumer>
          {tz => (
            <Consumer>
              {currentDate =>
                plain ? (
                  getTitle(date, locale, tz)
                ) : (
                  <Tooltip title={getTitle(date, locale, tz)}>
                    <ReactMoment from={currentDate} locale={locale} tz={tz}>
                      {date}
                    </ReactMoment>
                  </Tooltip>
                )
              }
            </Consumer>
          )}
        </TimezoneConsumer>
      )}
    </LocaleConsumer>
  );
};
BaseDate.displayName = "BaseDate";
export default BaseDate;
