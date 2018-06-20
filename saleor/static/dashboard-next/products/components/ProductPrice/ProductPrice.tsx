import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import Money from "../../../components/Money";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import Skeleton from "../../../components/Skeleton";

interface MoneyType {
  currency: string;
  amount: number;
}
interface ProductPriceProps {
  purchaseCost: {
    start: MoneyType;
    stop: MoneyType;
  };
  margin: {
    start: number;
    stop: number;
  };
}

const decorate = withStyles(theme => ({
  root: {
    "& td, & th": {
      paddingRight: theme.spacing.unit * 3
    }
  },
  textRight: {
    textAlign: "right" as "right"
  }
}));
const ProductPrice = decorate<ProductPriceProps>(
  ({ classes, margin, purchaseCost }) => (
    <Card>
      <PageHeader title={i18n.t("Pricing")} />
      <Table className={classes.root}>
        <TableBody>
          <TableRow>
            <TableCell>{i18n.t("Purchase cost")}</TableCell>
            <TableCell className={classes.textRight}>
              {purchaseCost ? (
                purchaseCost.start.amount === purchaseCost.stop.amount ? (
                  <>
                    <Money
                      amount={purchaseCost.start.amount}
                      currency={purchaseCost.start.currency}
                      typographyProps={{
                        component: "span",
                        style: { display: "inline" }
                      }}
                    />
                    {" - "}
                    <Money
                      amount={purchaseCost.start.amount}
                      currency={purchaseCost.start.currency}
                      typographyProps={{
                        component: "span",
                        style: { display: "inline" }
                      }}
                    />
                  </>
                ) : (
                  <Money
                    amount={purchaseCost.start.amount}
                    currency={purchaseCost.start.currency}
                    typographyProps={{
                      component: "span",
                      style: { display: "inline" }
                    }}
                  />
                )
              ) : (
                <Skeleton />
              )}
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>{i18n.t("Margin")}</TableCell>
            <TableCell className={classes.textRight}>
              {margin ? `${margin.start} % - ${margin.stop}%` : <Skeleton />}
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </Card>
  )
);
ProductPrice.displayName = "ProductPrice";
export default ProductPrice;
