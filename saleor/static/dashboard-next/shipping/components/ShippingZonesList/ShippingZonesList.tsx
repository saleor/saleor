import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import Checkbox from "@material-ui/core/Checkbox";
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
import TableFooter from "@material-ui/core/TableFooter";
import TableRow from "@material-ui/core/TableRow";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import TableHead from "../../../components/TableHead";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ICONBUTTON_SIZE } from "../../../theme";
import { ListActions, ListProps } from "../../../types";
import { ShippingZoneFragment } from "../../types/ShippingZoneFragment";

export interface ShippingZonesListProps extends ListProps, ListActions {
  shippingZones: ShippingZoneFragment[];
  onAdd: () => void;
  onRemove: (id: string) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    [theme.breakpoints.up("lg")]: {
      colCountries: {},
      colName: { width: 200 }
    },
    alignRight: {
      "&:last-child": {
        paddingRight: theme.spacing.unit
      },
      width: ICONBUTTON_SIZE + theme.spacing.unit / 2
    },
    colCountries: {},
    colName: {},
    row: {
      cursor: "pointer"
    }
  });
const ShippingZonesList = withStyles(styles, { name: "ShippingZonesList" })(
  ({
    classes,
    disabled,
    onAdd,
    onNextPage,
    onPreviousPage,
    onRemove,
    onRowClick,
    pageInfo,
    shippingZones,
    isChecked,
    selected,
    toggle,
    toolbar
  }: ShippingZonesListProps & WithStyles<typeof styles>) => (
    <Card>
      <CardTitle
        height="const"
        title={i18n.t("Shipping by zone")}
        toolbar={
          <Button color="primary" onClick={onAdd}>
            {i18n.t("Add shipping zone", {
              context: "button"
            })}
          </Button>
        }
      />
      <Table>
        <TableHead selected={selected} toolbar={toolbar}>
          <TableRow>
            <TableCell />
            <TableCell className={classes.colName}>
              {i18n.t("Name", { context: "object" })}
            </TableCell>
            <TableCell className={classes.colCountries}>
              {i18n.t("Countries", { context: "object" })}
            </TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={4}
              hasNextPage={pageInfo && !disabled ? pageInfo.hasNextPage : false}
              onNextPage={onNextPage}
              hasPreviousPage={
                pageInfo && !disabled ? pageInfo.hasPreviousPage : false
              }
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {renderCollection(
            shippingZones,
            shippingZone => {
              const isSelected = shippingZone
                ? isChecked(shippingZone.id)
                : false;

              return (
                <TableRow
                  className={classes.row}
                  hover={!!shippingZone}
                  key={shippingZone ? shippingZone.id : "skeleton"}
                  onClick={shippingZone && onRowClick(shippingZone.id)}
                  selected={isSelected}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      color="primary"
                      checked={isSelected}
                      disabled={disabled}
                      onClick={event => {
                        toggle(shippingZone.id);
                        event.stopPropagation();
                      }}
                    />
                  </TableCell>
                  <TableCell className={classes.colName}>
                    {maybe<React.ReactNode>(
                      () => shippingZone.name,
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.colCountries}>
                    {maybe<React.ReactNode>(
                      () => shippingZone.countries.length,
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.alignRight}>
                    <IconButton
                      color="primary"
                      disabled={disabled}
                      onClick={event => {
                        event.stopPropagation();
                        onRemove(shippingZone.id);
                      }}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              );
            },
            () => (
              <TableRow>
                <TableCell colSpan={4}>
                  {i18n.t("No shipping zones found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
ShippingZonesList.displayName = "ShippingZonesList";
export default ShippingZonesList;
