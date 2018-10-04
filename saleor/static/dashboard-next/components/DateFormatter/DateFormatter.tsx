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
  return (
    <LocaleConsumer>
      {locale => (
        <TimezoneConsumer>
          {tz => (
            <Consumer>
              {currentDate => (
                <Tooltip
                  title={moment(date)
                    .locale(locale)
                    .tz(tz)
                    .toLocaleString()}
                >
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
