import Tooltip from "@material-ui/core/Tooltip";
import * as moment from "moment-timezone";
import * as React from "react";
import ReactMoment from "react-moment";

import { LocaleConsumer } from "../Locale";
import { Consumer } from "./DateContext";

interface BaseDateProps {
  date: string;
  format: string;
  plain?: boolean;
  tz?: string;
}

const BaseDate: React.StatelessComponent<BaseDateProps> = ({
  date,
  format,
  plain,
  tz
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
    </LocaleConsumer>
  );
};
BaseDate.displayName = "BaseDate";
export default BaseDate;
