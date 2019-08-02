import Grow from "@material-ui/core/Grow";
import Popper from "@material-ui/core/Popper";
import { Theme } from "@material-ui/core/styles";
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
      marginTop: theme.spacing.unit * 2
    }
  }),
  {
    name: "ColumnPicker"
  }
);

const ColumnPicker: React.FC<ColumnPickerProps> = props => {
  const { className, columns, initial, selectedColumns } = props;
  const classes = useStyles(props);
  const anchor = React.useRef<HTMLDivElement>();
  const [isExpanded, setExpansionState] = React.useState(false);

  React.useEffect(() => {
    setTimeout(() => setExpansionState(!!initial), 100);
  }, []);

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
            <ColumnPickerContent
              columns={columns}
              selectedColumns={selectedColumns}
            />
          </Grow>
        )}
      </Popper>
    </div>
  );
};

export default ColumnPicker;
