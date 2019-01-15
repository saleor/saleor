import Card from "@material-ui/core/Card";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import { Container } from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { maybe, renderCollection, translatedTaxRates } from "../../../misc";
import { CountryList_shop_countries_vat_reducedRates } from "../../types/CountryList";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "9fr 4fr"
    },
    wideColumn: {
      width: "80%"
    }
  });

export interface CountryTaxesPageProps {
  countryName: string;
  taxCategories: CountryList_shop_countries_vat_reducedRates[];
}

const CountryTaxesPage = withStyles(styles, { name: "CountryTaxesPage" })(
  ({
    classes,
    countryName,
    taxCategories
  }: CountryTaxesPageProps & WithStyles<typeof styles>) => {
    const taxRates = translatedTaxRates();
    return (
      <Container width="md">
        <PageHeader
          title={
            countryName
              ? i18n.t("Tax Rates in {{ countryName }}", {
                  context: "page title",
                  countryName
                })
              : undefined
          }
        />
        <div className={classes.root}>
          <div>
            <Card>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell className={classes.wideColumn}>
                      {i18n.t("Category", { context: "object" })}
                    </TableCell>
                    <TableCell>
                      {i18n.t("Tax Rate", { context: "object" })}
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {renderCollection(
                    taxCategories,
                    taxCategory => (
                      <TableRow
                        key={taxCategory ? taxCategory.rateType : "skeleton"}
                      >
                        <TableCell>
                          {maybe<React.ReactNode>(
                            () => taxRates[taxCategory.rateType],
                            <Skeleton />
                          )}
                        </TableCell>
                        <TableCell>
                          {maybe<React.ReactNode>(
                            () => taxCategory.rate,
                            <Skeleton />
                          )}
                        </TableCell>
                      </TableRow>
                    ),
                    () => (
                      <TableRow>
                        <TableCell colSpan={2}>
                          {i18n.t("No reduced tax categories found")}
                        </TableCell>
                      </TableRow>
                    )
                  )}
                </TableBody>
              </Table>
            </Card>
          </div>
        </div>
      </Container>
    );
  }
);
CountryTaxesPage.displayName = "CountryTaxesPage";
export default CountryTaxesPage;
