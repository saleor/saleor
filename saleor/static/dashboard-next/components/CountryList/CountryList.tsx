import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
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
import DeleteIcon from "@material-ui/icons/Delete";
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
    iconCell: {
      "&:last-child": {
        paddingRight: 0
      },
      width: 48 + theme.spacing.unit / 2
    },
    indicator: {
      color: theme.palette.text.disabled,
      display: "inline-block",
      left: 0,
      marginRight: theme.spacing.unit * 2,
      position: "absolute"
    },
    offsetCell: {
      "&:first-child": {
        paddingLeft: theme.spacing.unit * 3
      },
      position: "relative"
    },
    pointer: {
      cursor: "pointer"
    },
    root: {
      "&:last-child": {
        paddingBottom: 0
      },
      paddingTop: 0
    },
    rotate: {
      transform: "rotate(180deg)"
    },
    textRight: {
      textAlign: "right"
    },
    toLeft: {
      "&:first-child": {
        paddingLeft: 0
      }
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
                color="primary"
                onClick={onCountryAssign}
              >
                {i18n.t("Assign countries")}
              </Button>
            }
          />
          <CardContent className={classes.root}>
            <Table>
              <TableBody>
                <TableRow className={classes.pointer} onClick={toggleCollapse}>
                  <TableCell
                    className={classNames(classes.wideColumn, classes.toLeft)}
                  >
                    {i18n.t("{{ number }} Countries", {
                      context: "number of countries",
                      number: maybe(() => countries.length.toString(), "...")
                    })}
                  </TableCell>
                  <TableCell
                    className={classNames(classes.textRight, classes.iconCell)}
                  >
                    <IconButton>
                      <ArrowDropDownIcon
                        className={classNames({
                          [classes.rotate]: !isCollapsed
                        })}
                      />
                    </IconButton>
                  </TableCell>
                </TableRow>
                {!isCollapsed &&
                  renderCollection(
                    countries,
                    (country, countryIndex) => (
                      <TableRow key={country ? country.code : "skeleton"}>
                        <TableCell className={classes.offsetCell}>
                          {maybe<React.ReactNode>(
                            () => (
                              <>
                                {(countryIndex === 0 ||
                                  countries[countryIndex].country[0] !==
                                    countries[countryIndex - 1].country[0]) && (
                                  <span className={classes.indicator}>
                                    {country.country[0]}
                                  </span>
                                )}
                                {country.country}
                              </>
                            ),
                            <Skeleton />
                          )}
                        </TableCell>
                        <TableCell
                          className={classNames(
                            classes.textRight,
                            classes.iconCell
                          )}
                        >
                          <IconButton
                            color="primary"
                            disabled={!country || disabled}
                            onClick={() => onCountryUnassign(country.code)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ),
                    () => (
                      <TableRow>
                        <TableCell className={classes.toLeft} colSpan={2}>
                          {emptyText}
                        </TableCell>
                      </TableRow>
                    )
                  )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </Toggle>
  )
);
export default CountryList;
