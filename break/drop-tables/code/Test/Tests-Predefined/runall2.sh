#!/bin/bash

echo "-----------------"
echo "Correctness Tests"
echo "-----------------"
passed=0
failed=0
for file in test{{1..9},arg{1..7}}.json; do
	output=$(./run.py $1 $file 2>&1)
	#echo $output
	result=$(echo $output | jq '.result')
	if [ "$result" == "true" ]; then
		((passed++))
		echo "$file: pass"
	else
		((failed++))
		echo "$file: fail"
	fi
done
total=$((passed + failed))
echo "Passed $passed/$total"
echo "Failed $failed/$total"

echo "--------------"
echo "Optional Tests"
echo "--------------"
passed=0
failed=0
for file in test{filter{1,2},func{1..3},let{1..3},timeout1}.json; do
	output=$(./run.py $1 $file 2>&1)
	#echo $output
	result=$(echo $output | jq '.result')
	if [ "$result" == "true" ]; then
		((passed++))
		echo "$file: pass"
	else
		((failed++))
		echo "$file: fail"
	fi
done
total=$((passed + failed))
echo "Passed $passed/$total"
echo "Failed $failed/$total"

echo "-----------------"
echo "Performance Tests"
echo "-----------------"
passed=0
failed=0
for file in testperf{1..8}.json; do
	output=$(./run.py $1 $file 2>&1)
	#echo $output
	result=$(echo $output | jq '.result')
	if [ "$result" == "true" ]; then
		((passed++))
		echo "$file: pass"
	else
		((failed++))
		echo "$file: fail"
	fi
done
total=$((passed + failed))
echo "Passed $passed/$total"
echo "Failed $failed/$total"



