import ClickAwayListener from "@material-ui/core/ClickAwayListener";
import Grow from "@material-ui/core/Grow";
import Popper from "@material-ui/core/Popper";
import { Theme } from "@material-ui/core/styles";
import { fade } from "@material-ui/core/styles/colorManipulator";
import makeStyles from "@material-ui/styles/makeStyles";
import React from "react";

import ColumnPickerButton from "./ColumnPickerButton";
import ColumnPickerContent, {
  ColumnPickerContentProps
} from "./ColumnPickerContent";

export interface ColumnPickerProps extends ColumnPickerContentProps {
  className?: string;
  initial?: boolean;
}

const useStyles = makeStyles(
  (theme: Theme) => ({
    popper: {
      boxShadow: `0px 5px 10px 0 ${fade(theme.palette.common.black, 0.05)}`,
      marginTop: theme.spacing.unit * 2,
      zIndex: 1
    }
  }),
  {
    name: "ColumnPicker"
  }
);

const ColumnPicker: React.FC<ColumnPickerProps> = props => {
  const {
    className,
    columns,
    initial = false,
    selectedColumns,
    onCancel,
    onColumnToggle,
    onReset,
    onSave
  } = props;
  const classes = useStyles(props);
  const anchor = React.useRef<HTMLDivElement>();
  const [isExpanded, setExpansionState] = React.useState(false);

  React.useEffect(() => {
    setTimeout(() => setExpansionState(initial), 100);
  }, []);

  const handleCancel = React.useCallback(() => {
    setExpansionState(false);
    onCancel();
  }, []);

  const handleSave = () => {
    setExpansionState(false);
    onSave();
  };

  return (
    <div ref={anchor} className={className}>
      <ColumnPickerButton
        active={isExpanded}
        onClick={() => setExpansionState(prevState => !prevState)}
      />
      <Popper
        className={classes.popper}
        open={isExpanded}
        anchorEl={anchor.current}
        transition
        disablePortal
        placement="bottom-end"
      >
        {({ TransitionProps, placement }) => (
          <Grow
            {...TransitionProps}
            style={{
              transformOrigin:
                placement === "bottom" ? "right bottom" : "right top"
            }}
          >
            <ClickAwayListener
              onClickAway={() => setExpansionState(false)}
              mouseEvent="onClick"
            >
              <ColumnPickerContent
                columns={columns}
                selectedColumns={selectedColumns}
                onCancel={handleCancel}
                onColumnToggle={onColumnToggle}
                onReset={onReset}
                onSave={handleSave}
              />
            </ClickAwayListener>
          </Grow>
        )}
      </Popper>
    </div>
  );
};

export default ColumnPicker;
