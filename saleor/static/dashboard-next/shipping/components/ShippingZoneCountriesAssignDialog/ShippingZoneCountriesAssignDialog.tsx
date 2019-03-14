import Button from "@material-ui/core/Button";
import Checkbox from "@material-ui/core/Checkbox";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
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
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import { filter } from "fuzzaldrin";
import * as React from "react";

import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../../../components/ConfirmButton/ConfirmButton";
import Form from "../../../components/Form";
import FormSpacer from "../../../components/FormSpacer";
import Hr from "../../../components/Hr";
import { ShopInfo_shop_countries } from "../../../components/Shop/types/ShopInfo";
import i18n from "../../../i18n";

interface FormData {
  countries: string[];
  query: string;
  restOfTheWorld: boolean;
}

export interface ShippingZoneCountriesAssignDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  countries: ShopInfo_shop_countries[];
  initial: string[];
  isDefault: boolean;
  open: boolean;
  onClose: () => void;
  onConfirm: (data: FormData) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    checkboxCell: {
      paddingLeft: 0
    },
    container: {
      maxHeight: 400
    },
    heading: {
      marginBottom: theme.spacing.unit * 2,
      marginTop: theme.spacing.unit * 2
    },
    table: {
      border: "1px solid " + theme.palette.grey[200]
    },
    wideCell: {
      width: "100%"
    }
  });
const ShippingZoneCountriesAssignDialog = withStyles(styles, {
  name: "ShippingZoneCountriesAssignDialog"
})(
  ({
    classes,
    confirmButtonState,
    isDefault,
    onClose,
    countries,
    open,
    initial,
    onConfirm
  }: ShippingZoneCountriesAssignDialogProps & WithStyles<typeof styles>) => {
    const initialForm: FormData = {
      countries: initial,
      query: "",
      restOfTheWorld: isDefault
    };
    return (
      <Dialog open={open} fullWidth maxWidth="sm">
        <Form initial={initialForm} onSubmit={onConfirm}>
          {({ data, change }) => {
            const countrySelectionMap = countries.reduce((acc, country) => {
              acc[country.code] = !!data.countries.find(
                selectedCountries => selectedCountries === country.code
              );
              return acc;
            }, {});

            return (
              <>
                <DialogTitle>{i18n.t("Assign Countries")}</DialogTitle>
                <DialogContent>
                  <Typography>
                    {i18n.t(
                      "Choose countries you want to add to shipping zone from list below"
                    )}
                  </Typography>
                  <FormSpacer />
                  <TextField
                    name="query"
                    value={data.query}
                    onChange={event => change(event, () => fetch(data.query))}
                    label={i18n.t("Search Countries", {
                      context: "country search input label"
                    })}
                    placeholder={i18n.t("Search by country name", {
                      context: "country search input placeholder"
                    })}
                    fullWidth
                  />
                </DialogContent>
                <Hr />

                <DialogContent className={classes.container}>
                  <Typography className={classes.heading} variant="subheading">
                    {i18n.t("Quick Pick")}
                  </Typography>
                  <Table className={classes.table}>
                    <TableBody>
                      <TableRow>
                        <TableCell className={classes.wideCell}>
                          {i18n.t("Rest of the World")}
                          <Typography variant="caption">
                            {i18n.t(
                              "If selected, this will add all of the countries not selected to other shipping zones"
                            )}
                          </Typography>
                        </TableCell>
                        <TableCell
                          padding="checkbox"
                          className={classes.checkboxCell}
                        >
                          <Checkbox
                            checked={data.restOfTheWorld}
                            onChange={() =>
                              change({
                                target: {
                                  name: "restOfTheWorld" as keyof FormData,
                                  value: !data.restOfTheWorld
                                }
                              } as any)
                            }
                          />
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </DialogContent>

                <DialogContent className={classes.container}>
                  <Typography className={classes.heading} variant="subheading">
                    {i18n.t("Countries A to Z", {
                      context: "country selection"
                    })}
                  </Typography>
                  <Table className={classes.table}>
                    <TableBody>
                      {filter(countries, data.query, {
                        key: "country"
                      }).map(country => {
                        const isChecked = countrySelectionMap[country.code];

                        return (
                          <TableRow key={country.code}>
                            <TableCell className={classes.wideCell}>
                              {country.country}
                            </TableCell>
                            <TableCell
                              padding="checkbox"
                              className={classes.checkboxCell}
                            >
                              <Checkbox
                                checked={isChecked}
                                onChange={() =>
                                  isChecked
                                    ? change({
                                        target: {
                                          name: "countries" as keyof FormData,
                                          value: data.countries.filter(
                                            selectedCountries =>
                                              selectedCountries !== country.code
                                          )
                                        }
                                      } as any)
                                    : change({
                                        target: {
                                          name: "countries" as keyof FormData,
                                          value: [
                                            ...data.countries,
                                            country.code
                                          ]
                                        }
                                      } as any)
                                }
                              />
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </DialogContent>
                <DialogActions>
                  <Button onClick={onClose}>
                    {i18n.t("Cancel", { context: "button" })}
                  </Button>
                  <ConfirmButton
                    transitionState={confirmButtonState}
                    color="primary"
                    variant="contained"
                    type="submit"
                  >
                    {i18n.t("Assign countries", { context: "button" })}
                  </ConfirmButton>
                </DialogActions>
              </>
            );
          }}
        </Form>
      </Dialog>
    );
  }
);
ShippingZoneCountriesAssignDialog.displayName =
  "ShippingZoneCountriesAssignDialog";
export default ShippingZoneCountriesAssignDialog;
