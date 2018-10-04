import Tooltip from "@material-ui/core/Tooltip";
import * as moment from "moment";
import * as React from "react";
import ReactMoment from "react-moment";

import { LocaleConsumer } from "../Locale";
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
        <Consumer>
          {currentDate => (
            <Tooltip
              title={moment(date)
                .locale(locale)
                .toLocaleString()}
            >
              <ReactMoment from={currentDate} locale={locale}>
                {date}
              </ReactMoment>
            </Tooltip>
          )}
        </Consumer>
      )}
    </LocaleConsumer>
  );
};

export default DateFormatter;
