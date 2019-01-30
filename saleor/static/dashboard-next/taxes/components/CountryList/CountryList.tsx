import Card from "@material-ui/core/Card";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as classNames from "classnames";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { CountryList_shop_countries } from "../../types/CountryList";

const styles = createStyles({
  tableRow: {
    cursor: "pointer"
  },
  textRight: {
    textAlign: "right"
  }
});

interface CountryListProps extends WithStyles<typeof styles> {
  countries: CountryList_shop_countries[];
  onRowClick: (code: string) => void;
}

const CountryList = withStyles(styles, { name: "CountryList" })(
  ({ classes, onRowClick, countries }: CountryListProps) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>
              {i18n.t("Country Code", { context: "object" })}
            </TableCell>
            <TableCell>
              {i18n.t("Country Name", { context: "object" })}
            </TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Reduced Tax Rates", { context: "object" })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {renderCollection(
            countries,
            country => (
              <TableRow
                className={classNames({
                  [classes.tableRow]: !!country
                })}
                hover={!!country}
                onClick={!!country ? () => onRowClick(country.code) : undefined}
                key={country ? country.code : "skeleton"}
              >
                <TableCell>
                  {maybe<React.ReactNode>(() => country.code, <Skeleton />)}
                </TableCell>
                <TableCell>
                  {maybe<React.ReactNode>(() => country.country, <Skeleton />)}
                </TableCell>
                <TableCell className={classes.textRight}>
                  {maybe<React.ReactNode>(
                    () => country.vat.reducedRates.length,
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={3}>
                  {i18n.t("No countries found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
CountryList.displayName = "CountryList";
export default CountryList;
