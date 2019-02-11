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
import TableRow from "@material-ui/core/TableRow";
import ArrowDropDownIcon from "@material-ui/icons/ArrowDropDown";
import CloseIcon from "@material-ui/icons/Close";
import classNames from "classnames";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { VoucherDetails_voucher } from "../../types/VoucherDetails";

export interface VoucherCountriesProps {
  disabled: boolean;
  voucher: VoucherDetails_voucher;
  onCountryAssign: () => void;
  onCountryUnassign: (country: string) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    arrow: {
      marginRight: theme.spacing.unit * 1.5
    },
    pointer: {
      cursor: "pointer"
    },
    rotate: {
      transform: "rotate(180deg)"
    },
    textRight: {
      textAlign: "right"
    },
    wideColumn: {
      width: "100%"
    }
  });

const VoucherCountries = withStyles(styles, {
  name: "VoucherCountries"
})(
  ({
    classes,
    disabled,
    voucher,
    onCountryAssign,
    onCountryUnassign
  }: VoucherCountriesProps & WithStyles<typeof styles>) => (
    <Toggle>
      {(isCollapsed, { toggle: toggleCollapse }) => (
        <Card>
          <CardTitle
            title={i18n.t("Countries assigned to {{ voucherName }}", {
              voucherName: maybe(() => voucher.name)
            })}
            toolbar={
              <Button
                variant="flat"
                color="secondary"
                onClick={onCountryAssign}
              >
                {i18n.t("Assign countries")}
              </Button>
            }
          />
          <Table>
            <TableBody>
              <TableRow className={classes.pointer} onClick={toggleCollapse}>
                <TableCell className={classes.wideColumn}>
                  {i18n.t("{{ number }} Countries", {
                    context: "number of countries",
                    number: maybe(
                      () => voucher.countries.length.toString(),
                      "..."
                    )
                  })}
                </TableCell>
                <TableCell className={classes.textRight}>
                  <ArrowDropDownIcon
                    className={classNames({
                      [classes.arrow]: true,
                      [classes.rotate]: !isCollapsed
                    })}
                  />
                </TableCell>
              </TableRow>
              {!isCollapsed &&
                renderCollection(
                  maybe(() => voucher.countries),
                  country => (
                    <TableRow key={country ? country.code : "skeleton"}>
                      <TableCell>
                        {maybe<React.ReactNode>(
                          () => country.country,
                          <Skeleton />
                        )}
                      </TableCell>
                      <TableCell className={classes.textRight}>
                        <IconButton
                          disabled={!country || disabled}
                          onClick={() => onCountryUnassign(country.code)}
                        >
                          <CloseIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ),
                  () => (
                    <TableRow>
                      <TableCell colSpan={2}>
                        {i18n.t("No categories found")}
                      </TableCell>
                    </TableRow>
                  )
                )}
            </TableBody>
          </Table>
        </Card>
      )}
    </Toggle>
  )
);
export default VoucherCountries;
