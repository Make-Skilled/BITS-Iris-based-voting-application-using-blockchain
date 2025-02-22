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

    struct Poll{
      uint id;
      string partyName;
      string partyLeader;
      string symbolPath;
    }

    uint private pollIdCounter; // Auto-incrementing poll ID
    mapping(uint => Poll) private polls; // Mapping from poll ID to Poll struct
    Poll[] public allPolls;

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

  // Function to add a new poll
    function addPoll(string memory _partyName, string memory _partyLeader, string memory _symbolPath) public {
        pollIdCounter++; // Auto-increment ID
        polls[pollIdCounter] = Poll(pollIdCounter, _partyName, _partyLeader, _symbolPath);
        allPolls.push(Poll(pollIdCounter, _partyName, _partyLeader, _symbolPath));
    }

    // Function to get a poll by ID
    function getPoll(uint _id) public view returns (uint, string memory, string memory, string memory) {
        require(_id > 0 && _id <= pollIdCounter, "Poll ID does not exist");
        Poll memory poll = polls[_id];
        return (poll.id, poll.partyName, poll.partyLeader, poll.symbolPath);
    }

    function getAllPolls() public view returns (Poll[] memory) {
        return allPolls;
    }
}
