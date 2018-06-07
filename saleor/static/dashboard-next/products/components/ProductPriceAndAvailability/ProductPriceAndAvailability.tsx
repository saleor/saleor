import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import green from "@material-ui/core/colors/green";
import red from "@material-ui/core/colors/red";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import ControlledSwitch from "../../../components/ControlledSwitch";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface ProductPriceAndAvailabilityProps {
  grossMargin?: {
    start: number;
    stop: number;
  };
  salePrice?: {
    start: string;
    stop: string;
  };
  purchaseCost?: {
    start: string;
    stop: string;
  };
  isPublished?: boolean;
  isAvailable?: boolean;
  onPublish(event: React.ChangeEvent<any>);
}

const decorate = withStyles(theme => ({
  greenText: {
    color: green[500]
  },
  leftCell: {
    paddingRight: theme.spacing.unit
  },
  redText: {
    color: red[500]
  },
  rightCell: {
    paddingLeft: theme.spacing.unit,
    textAlign: "right" as "right"
  }
}));
export const ProductPriceAndAvailability = decorate<
  ProductPriceAndAvailabilityProps
>(
  ({
    classes,
    grossMargin,
    salePrice,
    purchaseCost,
    isPublished,
    isAvailable,
    onPublish
  }) => (
    <Card>
      <CardContent>
        <ControlledSwitch
          onChange={onPublish}
          uncheckedLabel={
            isPublished === undefined || isPublished === null
              ? " "
              : i18n.t("Draft")
          }
          label={i18n.t("Published")}
          checked={!(isPublished === undefined || isPublished === null)}
          disabled={isPublished === undefined || isPublished === null}
        />
        <Typography>
          {isAvailable === undefined || isAvailable === null ? (
            <Skeleton />
          ) : isAvailable ? (
            <span className={classes.greenText}>{i18n.t("Available")}</span>
          ) : (
            <span className={classes.redText}>{i18n.t("Unavailable")}</span>
          )}
        </Typography>
      </CardContent>
      <Table>
        <TableBody>
          <TableRow>
            <TableCell className={classes.leftCell}>
              {i18n.t("Sale price")}
            </TableCell>
            <TableCell className={classes.rightCell}>
              {salePrice ? (
                <span>
                  {salePrice.start} - {salePrice.stop}
                </span>
              ) : (
                <Skeleton />
              )}
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell className={classes.leftCell}>
              {i18n.t("Purchase cost")}
            </TableCell>
            <TableCell className={classes.rightCell}>
              {purchaseCost ? (
                <span>
                  {purchaseCost.start} - {purchaseCost.stop}
                </span>
              ) : (
                <Skeleton />
              )}
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell className={classes.leftCell}>
              {i18n.t("Gross margin")}
            </TableCell>
            <TableCell className={classes.rightCell}>
              {grossMargin ? (
                <span>
                  {grossMargin.start}% - {grossMargin.stop}%
                </span>
              ) : (
                <Skeleton />
              )}
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </Card>
  )
);
ProductPriceAndAvailability.displayName = "ProductPriceAndAvailability";
export default ProductPriceAndAvailability;
