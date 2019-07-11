import { media, styled } from "@styles";

export const PaymentForm = styled.form`
  width: 100%;
`;

export const PaymentInput = styled.div`
  width: 100%;
`;
PaymentInput.displayName = "S.PaymentInput";

export const Grid = styled.div`
  display: flex;
  justify-content: space-between;
  ${media.smallScreen`
     flex-direction: column;
  `}
  & > div {
    padding-right: ${props => props.theme.spacing.spacer};
    &:last-child {
      padding-right: 0;
    }
    ${media.smallScreen`
      padding-right:  0;
      
    `}
  }
`;
