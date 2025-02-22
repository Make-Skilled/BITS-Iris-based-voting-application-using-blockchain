// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;

contract voting {

  struct Voter {
        string fullName;
        string aadharNumber;
        string irisImagePath; // Stores only the image path, not the actual image
        string email;
        string password;
    }

    mapping(string => Voter) public voters;
    string[] public voterAadhars;

    function registerVoter(string memory _fullName, string memory _aadharNumber, string memory _irisImagePath,string memory email,string memory password) public {
        require(bytes(voters[_aadharNumber].aadharNumber).length == 0, "Voter already registered this aadhar number");

        voters[_aadharNumber] = Voter({
            fullName: _fullName,
            aadharNumber: _aadharNumber,
            irisImagePath: _irisImagePath,
            email:email,
            password:password
        });

        voterAadhars.push(_aadharNumber);
  }

    function getVoter(string memory aadhar) public view returns (string memory, string memory, string memory,string memory,string memory) {
        require(bytes(voters[aadhar].aadharNumber).length > 0, "Voter not registered");

        Voter memory voter = voters[aadhar];
        return (voter.fullName, voter.aadharNumber, voter.irisImagePath,voter.email,voter.password);
    }
}
