import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as classNames from "classnames";
import * as React from "react";

import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import IconButton from "@material-ui/core/IconButton";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import AddIcon from "@material-ui/icons/Add";
import DeleteIcon from "@material-ui/icons/Delete";
import Hr from "../../../components/Hr";

import CardTitle from "../../../components/CardTitle";
import Toggle from "../../../components/Toggle";

import i18n from "../../../i18n";

const styles = (theme: Theme) =>
  createStyles({
    addSubCat: {
      marginTop: ".5rem",
      padding: "0"
    },
    deleteIcon: {
      alignSelf: "end",
      justifySelf: "center"
    },
    helperText: {
      marginBottom: theme.spacing.unit * 4
    },
    inputGrid: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "5fr 8fr 30px",
      marginBottom: "1rem"
    },
    root: {
      "&:last-child": {
        paddingBottom: ".5rem"
      },
      paddingBottom: "0px"
    }
  });

interface CategoryCreateSubcategoriesProps extends WithStyles<typeof styles> {
  disabled: boolean;
}

export const CategoryCreateSubcategories = withStyles(styles, {
  name: "CategoryCreateSubcategories"
})(({ classes, disabled }: CategoryCreateSubcategoriesProps) => {
  return (
    <Toggle>
      {(toggled, { toggle }) => (
        <Card>
          <CardTitle
            title={i18n.t("Subcategories")}
            toolbar={
              <Button
                color={toggled ? "default" : "secondary"}
                variant="text"
                onClick={toggle}
                disabled={disabled}
              >
                {toggled ? i18n.t("Cancel") : i18n.t("Add subcategory")}
              </Button>
            }
          />
          <CardContent className={classNames({ [classes.root]: toggled })}>
            <Typography
              className={classNames({ [classes.helperText]: toggled })}
            >
              {i18n.t("Add subcategories to help you organize your products")}
            </Typography>
            {toggled && (
              <>
                <div className={classes.inputGrid}>
                  <TextField label={i18n.t("Category Name")} />
                  <TextField label={i18n.t("Category Description")} />
                  <IconButton className={classes.deleteIcon} color="primary">
                    <DeleteIcon />
                  </IconButton>
                </div>

                <Hr />
                <Button
                  variant="text"
                  color="primary"
                  className={classes.addSubCat}
                >
                  {i18n.t("Add subcategory")}
                  <AddIcon />
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </Toggle>
  );
});
CategoryCreateSubcategories.displayName = "CategoryCreateSubcategories";
export default CategoryCreateSubcategories;
