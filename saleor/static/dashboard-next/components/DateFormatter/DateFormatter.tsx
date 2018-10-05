import Tooltip from "@material-ui/core/Tooltip";
import * as moment from "moment-timezone";
import * as React from "react";
import ReactMoment from "react-moment";

import { LocaleConsumer } from "../Locale";
import { TimezoneConsumer } from "../Timezone";
import { Consumer } from "./DateContext";

interface DateFormatterProps {
  date: string;
}

const DateFormatter: React.StatelessComponent<DateFormatterProps> = ({
  date
}) => {
  const getTitle = (value: string, locale?: string, tz?: string) => {
    let date = moment(value).locale(locale);
    if (tz !== undefined) {
      date = date.tz(tz);
    }
    return date.toLocaleString();
  };
  return (
    <LocaleConsumer>
      {locale => (
        <TimezoneConsumer>
          {tz => (
            <Consumer>
              {currentDate => (
                <Tooltip title={getTitle(date, locale, tz)}>
                  <ReactMoment from={currentDate} locale={locale} tz={tz}>
                    {date}
                  </ReactMoment>
                </Tooltip>
              )}
            </Consumer>
          )}
        </TimezoneConsumer>
      )}
    </LocaleConsumer>
  );
};

export default DateFormatter;
