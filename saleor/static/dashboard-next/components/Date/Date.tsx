import Tooltip from "@material-ui/core/Tooltip";
import * as moment from "moment-timezone";
import * as React from "react";

import useDateLocalize from "@saleor-hooks/useDateLocalize";
import { LocaleConsumer } from "../Locale";
import { Consumer } from "./DateContext";

interface DateProps {
  date: string;
  plain?: boolean;
}

export const Date: React.FC<DateProps> = ({ date, plain }) => {
  const localizeDate = useDateLocalize();
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
              localizeDate(date)
            ) : (
              <Tooltip title={localizeDate(date)}>
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
