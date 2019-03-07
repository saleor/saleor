import Tooltip from "@material-ui/core/Tooltip";
import * as moment from "moment-timezone";
import * as React from "react";

import { LocaleConsumer } from "../Locale";
import { Consumer } from "./DateContext";

interface DateProps {
  date: string;
  plain?: boolean;
}

export const Date: React.StatelessComponent<DateProps> = ({ date, plain }) => {
  const getTitle = (value: string, locale: string) =>
    moment(value)
      .locale(locale)
      .format("ll");
  const getHumanized = (value: string, locale: string, currentDate: number) =>
    moment(value)
      .locale(locale)
      .from(currentDate);

  return (
    <LocaleConsumer>
      {locale => (
        <Consumer>
          {currentDate =>
            plain ? (
              getTitle(date, locale)
            ) : (
              <Tooltip title={getTitle(date, locale)}>
                <time dateTime={date}>
                  {getHumanized(date, locale, currentDate)}
                </time>
              </Tooltip>
            )
          }
        </Consumer>
      )}
    </LocaleConsumer>
  );
};
Date.displayName = "Date";
export default Date;
