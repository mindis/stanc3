  $ $TESTDIR/../../..//../../_build/default/stanc.exe --auto-format "$TESTDIR/../../..//function-signatures/math/matrix/trace.stan"
  data {
    int d_int;
    matrix[d_int, d_int] d_matrix;
  }
  transformed data {
    real transformed_data_real;
    transformed_data_real <- trace(d_matrix);
  }
  parameters {
    real y_p;
    matrix[d_int, d_int] p_matrix;
  }
  transformed parameters {
    real transformed_param_real;
    transformed_param_real <- trace(d_matrix);
    transformed_param_real <- trace(p_matrix);
  }
  model {
    y_p ~ normal(0, 1);
  }
  
