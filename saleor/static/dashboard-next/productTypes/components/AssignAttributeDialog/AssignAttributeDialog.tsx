import Button from "@material-ui/core/Button";
import CircularProgress from "@material-ui/core/CircularProgress";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogContentText from "@material-ui/core/DialogContentText";
import DialogTitle from "@material-ui/core/DialogTitle";
import { Theme } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import makeStyles from "@material-ui/styles/makeStyles";
import * as React from "react";
import InfiniteScroll from "react-infinite-scroller";

import Checkbox from "@saleor/components/Checkbox";
import ConfirmButton, {
  ConfirmButtonTransitionState
} from "@saleor/components/ConfirmButton";
import useModalDialogErrors from "@saleor/hooks/useModalDialogErrors";
import useModalDialogOpen from "@saleor/hooks/useModalDialogOpen";
import useSearchQuery from "@saleor/hooks/useSearchQuery";
import i18n from "@saleor/i18n";
import { maybe, renderCollection } from "@saleor/misc";
import { FetchMoreProps } from "@saleor/types";
import { SearchAttributes_productType_availableAttributes_edges_node } from "../../containers/SearchAttributes/types/SearchAttributes";

const useStyles = makeStyles((theme: Theme) => ({
  checkboxCell: {
    paddingLeft: 0
  },
  loadMoreLoaderContainer: {
    alignItems: "center",
    display: "flex",
    height: theme.spacing.unit * 3,
    justifyContent: "center"
  },
  scrollArea: {
    overflowY: "scroll"
  },
  wideCell: {
    width: "100%"
  }
}));

export interface AssignAttributeDialogProps extends FetchMoreProps {
  confirmButtonState: ConfirmButtonTransitionState;
  errors: string[];
  open: boolean;
  attributes: SearchAttributes_productType_availableAttributes_edges_node[];
  selected: string[];
  onClose: () => void;
  onOpen: () => void;
  onSubmit: () => void;
  onToggle: (id: string) => void;
}

const AssignAttributeDialog: React.FC<AssignAttributeDialogProps> = ({
  attributes,
  confirmButtonState,
  errors: apiErrors,
  hasMore,
  loading,
  open,
  selected,
  onClose,
  onFetch,
  onFetchMore,
  onOpen,
  onSubmit,
  onToggle
}: AssignAttributeDialogProps) => {
  const classes = useStyles({});
  const [query, onQueryChange, resetQuery] = useSearchQuery(onFetch);
  const errors = useModalDialogErrors(apiErrors, open);

  useModalDialogOpen(open, {
    onClose: resetQuery,
    onOpen
  });

  return (
    <Dialog onClose={onClose} open={open} fullWidth maxWidth="sm">
      <DialogTitle>{i18n.t("Assign Attribute")}</DialogTitle>
      <DialogContent>
        <TextField
          name="query"
          value={query}
          onChange={onQueryChange}
          label={i18n.t("Search Attributes", {
            context: "attribute search input label"
          })}
          placeholder={i18n.t("Search by attribute name", {
            context: "attribute search input placeholder"
          })}
          fullWidth
          InputProps={{
            autoComplete: "off",
            endAdornment: loading && <CircularProgress size={16} />
          }}
        />
      </DialogContent>
      <DialogContent className={classes.scrollArea}>
        <InfiniteScroll
          pageStart={0}
          loadMore={onFetchMore}
          hasMore={hasMore}
          useWindow={false}
          loader={
            <div className={classes.loadMoreLoaderContainer}>
              <CircularProgress size={16} />
            </div>
          }
          threshold={100}
          key="infinite-scroll"
        >
          <Table key="table">
            <TableBody>
              {renderCollection(
                attributes,
                attribute => {
                  if (!attribute) {
                    return null;
                  }
                  const isChecked = !!selected.find(
                    selectedAttribute => selectedAttribute === attribute.id
                  );

                  return (
                    <TableRow key={maybe(() => attribute.id)}>
                      <TableCell
                        padding="checkbox"
                        className={classes.checkboxCell}
                      >
                        <Checkbox
                          checked={isChecked}
                          onChange={() => onToggle(attribute.id)}
                        />
                      </TableCell>
                      <TableCell className={classes.wideCell}>
                        {attribute.name}
                        <Typography variant="caption">
                          {attribute.slug}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  );
                },
                () =>
                  !loading && (
                    <TableRow>
                      <TableCell colSpan={2}>
                        {i18n.t("No results found")}
                      </TableCell>
                    </TableRow>
                  )
              )}
            </TableBody>
          </Table>
        </InfiniteScroll>
      </DialogContent>
      {errors.length > 0 && (
        <DialogContent>
          {errors.map((error, errorIndex) => (
            <DialogContentText color="error" key={errorIndex}>
              {error}
            </DialogContentText>
          ))}
        </DialogContent>
      )}
      <DialogActions>
        <Button onClick={onClose}>
          {i18n.t("Cancel", { context: "button" })}
        </Button>
        <ConfirmButton
          transitionState={confirmButtonState}
          color="primary"
          variant="contained"
          type="submit"
          onClick={onSubmit}
        >
          {i18n.t("Assign attributes", { context: "button" })}
        </ConfirmButton>
      </DialogActions>
    </Dialog>
  );
};
AssignAttributeDialog.displayName = "AssignAttributeDialog";
export default AssignAttributeDialog;
