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

import CardTitle from "../../components/CardTitle";
import Skeleton from "../../components/Skeleton";
import Toggle from "../../components/Toggle";
import i18n from "../../i18n";
import { maybe, renderCollection } from "../../misc";
import { CountryFragment } from "../../taxes/types/CountryFragment";

export interface CountryListProps {
  countries: CountryFragment[];
  disabled: boolean;
  emptyText: React.ReactNode;
  title: React.ReactNode;
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

const CountryList = withStyles(styles, {
  name: "CountryList"
})(
  ({
    classes,
    countries,
    disabled,
    emptyText,
    title,
    onCountryAssign,
    onCountryUnassign
  }: CountryListProps & WithStyles<typeof styles>) => (
    <Toggle initial={true}>
      {(isCollapsed, { toggle: toggleCollapse }) => (
        <Card>
          <CardTitle
            title={title}
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
                    number: maybe(() => countries.length.toString(), "...")
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
                  countries,
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
                      <TableCell colSpan={2}>{emptyText}</TableCell>
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
export default CountryList;
