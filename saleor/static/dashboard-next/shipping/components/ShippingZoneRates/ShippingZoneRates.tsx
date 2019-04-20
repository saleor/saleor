import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import IconButton from "@material-ui/core/IconButton";
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
import DeleteIcon from "@material-ui/icons/Delete";
import EditIcon from "@material-ui/icons/Edit";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Money from "../../../components/Money";
import MoneyRange from "../../../components/MoneyRange";
import Skeleton from "../../../components/Skeleton";
import WeightRange from "../../../components/WeightRange";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ICONBUTTON_SIZE } from "../../../theme";
import { ShippingZoneDetailsFragment_shippingMethods } from "../../types/ShippingZoneDetailsFragment";

export interface ShippingZoneRatesProps {
  disabled: boolean;
  rates: ShippingZoneDetailsFragment_shippingMethods[];
  variant: "price" | "weight";
  onRateAdd: () => void;
  onRateEdit: (id: string) => void;
  onRateRemove: (id: string) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    alignRight: {
      "&:last-child": {
        paddingRight: 0
      },
      paddingRight: 0,
      width: ICONBUTTON_SIZE + theme.spacing.unit / 2
    },
    nameColumn: {
      width: 300
    },
    valueColumn: {
      width: 300
    }
  });
const ShippingZoneRates = withStyles(styles, { name: "ShippingZoneRates" })(
  ({
    classes,
    disabled,
    onRateAdd,
    onRateEdit,
    onRateRemove,
    rates,
    variant
  }: ShippingZoneRatesProps & WithStyles<typeof styles>) => (
    <Card>
      <CardTitle
        height="const"
        title={
          variant === "price"
            ? i18n.t("Price Based Rates")
            : i18n.t("Weight Based Rates")
        }
        toolbar={
          <Button color="primary" onClick={onRateAdd}>
            {i18n.t("Add rate", {
              context: "button"
            })}
          </Button>
        }
      />
      <Table>
        <TableHead>
          <TableRow>
            <TableCell className={classes.nameColumn}>
              {i18n.t("Name", { context: "object" })}
            </TableCell>
            <TableCell className={classes.valueColumn}>
              {variant === "price"
                ? i18n.t("Value Range", { context: "object" })
                : i18n.t("Weight Range", { context: "object" })}
            </TableCell>
            <TableCell className={classes.nameColumn}>
              {i18n.t("Price", { context: "object" })}
            </TableCell>
            <TableCell />
            <TableCell />
          </TableRow>
        </TableHead>
        <TableBody>
          {renderCollection(
            rates,
            rate => (
              <TableRow
                hover={!!rate}
                key={rate ? rate.id : "skeleton"}
                onClick={!!rate ? () => onRateEdit(rate.id) : undefined}
              >
                <TableCell className={classes.nameColumn}>
                  {maybe<React.ReactNode>(() => rate.name, <Skeleton />)}
                </TableCell>
                <TableCell>
                  {maybe<React.ReactNode>(
                    () =>
                      variant === "price" ? (
                        <MoneyRange
                          from={rate.minimumOrderPrice}
                          to={rate.maximumOrderPrice}
                        />
                      ) : (
                        <WeightRange
                          from={rate.minimumOrderWeight}
                          to={rate.maximumOrderWeight}
                        />
                      ),
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell>
                  {maybe<React.ReactNode>(
                    () => (
                      <Money money={rate.price} />
                    ),
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell className={classes.alignRight}>
                  <IconButton
                    color="primary"
                    disabled={disabled}
                    onClick={event => {
                      event.stopPropagation();
                      onRateEdit(rate.id);
                    }}
                  >
                    <EditIcon />
                  </IconButton>
                </TableCell>
                <TableCell className={classes.alignRight}>
                  <IconButton
                    color="primary"
                    disabled={disabled}
                    onClick={event => {
                      event.stopPropagation();
                      onRateRemove(rate.id);
                    }}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={5}>
                  {i18n.t("No shipping rates found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
ShippingZoneRates.displayName = "ShippingZoneRates";
export default ShippingZoneRates;
