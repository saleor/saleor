#!/usr/local/bin/perl

#author krgupta

#Modifying XSD to add wildcard character 
#Adding paymentScheduleTypeInterval type to overcome pyxb's anonymous complex type issue

$input_file = $ARGV[0];
$intermediate_file = $ARGV[1];
$output_file = $ARGV[2];
$inp_cmd = "dos2unix $input_file\n";

open(INP,"<$input_file") or die "Cannot open $input_file for reading:$!\n";
open(OUP,">$intermediate_file") or die "Cannot open $intermediate_file for writing\n";
$appd_line = "\<xs:any minOccurs=\"0\" maxOccurs=\"unbounded\" processContents=\"lax\" namespace=\"##any\" \/\>\n";
while(<INP>){
        $line=$_;
		if($line =~ /(\t+|\s+)(\<\/xs:sequence)(.*)/){
			$new_line = $1 . "\t" . $appd_line . $line;
			print OUP "$new_line";	 			
		}
		else{
			print OUP "$line";
		}
}		
close(OUP);
close(INP);
#print "$intermediate_file created from AnetApiSchema.xsd\n"; #uncomment for debugging

# Using intermediate file as input
open(INPUT,"<$intermediate_file") or die "Cannot open $intermediate_file for reading:$!\n";
$inp_cmd = "dos2unix $intermediate_file\n";

open(OUTPUT,">$output_file") or die "Cannot open $output_file for writing\n";
$matchline = '<xs:complexType name="paymentScheduleType">';

$i=0;$j=0;
@lines1=();
@lines2=();
while(<INPUT>){
	$readline=$_;
	if($readline =~ /$matchline/){
		($new_readline = $readline) =~ s/paymentScheduleType/paymentScheduleTypeInterval/g;
		$lines1[$i] = $new_readline;
		$i++;
		$lines2[$j] = $readline;
		$j++;
		$readline = <INPUT>;
		while($readline !~ /<xs:complexType/){
			$lines2[$j] = $readline;
			$readline = <INPUT>;
			$j++;
		}
		$readline = <INPUT>;
		while($readline !~ /<\/xs:complexType>/){
			($lines1[$i] = $readline) =~ s/\t\t\t//;
			$i++;
			$readline = <INPUT>;
		}
		($lines1[$i] = $readline) =~ s/\t\t\t//;
		$lines1[$i+1] = "\t<!-- ===================================================== -->\n\n";
		$deleteline = <INPUT>;
		
		$lines2[$j-1] =~ s/minOccurs=\"0\"/minOccurs=\"0\" type=\"anet:paymentScheduleTypeInterval\" \//g;
		print OUTPUT @lines1;
		print OUTPUT @lines2;
	}
	else{
		print OUTPUT "$readline";
	}
}
close(OUTPUT);



