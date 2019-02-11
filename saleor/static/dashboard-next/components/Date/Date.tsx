import Tooltip from "@material-ui/core/Tooltip";
import * as moment from "moment-timezone";
import * as React from "react";
import ReactMoment from "react-moment";

import { LocaleConsumer } from "../Locale";
import { TimezoneConsumer } from "../Timezone";
import { Consumer } from "./DateContext";

interface DateProps {
  date: string;
  plain?: boolean;
}

const Date: React.StatelessComponent<DateProps> = ({ date, plain }) => {
  const getTitle = (value: string, locale?: string, tz?: string) => {
    let date = moment(value).locale(locale);
    if (tz !== undefined) {
      date = date.tz(tz);
    }
    return date.format("LL");
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
Date.displayName = "Date";
export default Date;
